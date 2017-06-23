import datetime
import json

from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash,
    current_app,
    jsonify
)

from flask_login import login_required, current_user

from application.cms import cms_blueprint
from application.cms.utils import internal_user_required
from application.cms.forms import (
    PageForm,
    MeasurePageForm,
    DimensionForm,
    MeasurePageRequiredForm,
    DimensionRequiredForm
)
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException, DimensionAlreadyExists
from application.cms.exceptions import PageExistsException
from application.cms.models import publish_status, Meta, Page, Dimension
from application.cms.page_service import page_service


@cms_blueprint.route('/')
@internal_user_required
@login_required
def index():
    pages = page_service.get_topics()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/overview', methods=['GET'])
@internal_user_required
@login_required
def overview():
    # List all topic pages
    pages = page_service.get_pages_by_type('topic')
    return render_template('cms/overview.html', pages=pages)


@cms_blueprint.route('/<topic>/<subtopic>/measure/new', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_measure_page(topic, subtopic):
    topic_page = page_service.get_page(topic)
    subtopic_page = page_service.get_page(subtopic)
    form = MeasurePageForm()
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        try:
            if form.validate():
                page = page_service.create_page(page_type='measure',
                                                parent=subtopic_page.guid,
                                                data=form.data,
                                                user=current_user.email)

                message = 'Created page {}'.format(page.title)
                flash(message, 'info')
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic_page.guid,
                                        subtopic=subtopic_page.guid,
                                        measure=page.guid))
            else:
                flash(form.errors, 'error')
        except PageExistsException:
            flash('A page with that code already exists', 'error')
            return redirect(url_for("cms.create_measure_page",
                                    topic=topic,
                                    subtopic=subtopic))

    return render_template("cms/new_measure_page.html",
                           form=form,
                           topic=topic_page,
                           subtopic=subtopic_page)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_dimension(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_dimension(measure_page, dimension.guid, current_user.email)

    message = 'Deleted dimension {}'.format(dimension.title)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_measure_page(topic, subtopic, measure):
    try:
        subtopic_page = page_service.get_page(subtopic)
        topic_page = page_service.get_page(topic)
        page = page_service.get_page(measure)

    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm(obj=page)
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        if form.validate():
            message = 'User %s updated page. %s' % (current_user.email, page.guid)
            page_service.update_page(page, data=form.data, message=message)
            message = 'Updated page {}'.format(page.title)
            flash(message, 'info')
        else:
            print("NOT VALIDATED")
            print(form.errors)

    current_status = page.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status + 1]

    context = {
        'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
    }

    _build_site_if_required(context, page, current_app.config['BETA_PUBLICATION_STATES'])

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic_overview(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    if page.children:
        ordered_subtopics = []
        for st in page.subtopics:
            for c in page.children:
                if c.guid == st:
                    ordered_subtopics.append(c)

        children = ordered_subtopics if ordered_subtopics else page.children
    context = {'page': page,
               'children': children}
    return render_template("cms/topic_overview.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>')
@internal_user_required
@login_required
def subtopic_overview(topic, subtopic):
    try:
        page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    topic_page = page_service.get_page(topic)
    ordered_subtopics = []

    if page.children:
        for st in page.subtopics:
            for c in page.children:
                if c.guid == st:
                    ordered_subtopics.append(c)

    children = ordered_subtopics if ordered_subtopics else page.children

    # if any pages left over after ordering by subtopic add them to the list
    for p in page.children:
        if p not in children:
            children.append(p)

    context = {'page': page,
               'topic': topic_page,
               'children': children}

    return render_template("cms/subtopic_overview.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/upload', methods=['POST'])
@internal_user_required
@login_required
def upload_file(topic, subtopic, measure):
    file = request.files['file']
    if file.filename == '':
        return json.dumps({'status': 'BAD REQUEST'}), 400
    else:
        page = page_service.get_page(measure)
        page_service.upload_data(measure, file)
        return json.dumps({'status': 'OK', 'file': file.filename}), 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/publish', methods=['GET'])
@internal_user_required
@login_required
def publish_page(topic, subtopic, measure):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page(measure)
    except PageNotFoundException:
        abort(404)

    # TODO needs a publication date <= now as well as accepted to be published to static site
    build = True if measure_page.status in current_app.config.get('BETA_PUBLICATION_STATES', []) else False

    status = measure_page.status.replace('_', ' ').title()

    measure_form = MeasurePageRequiredForm(obj=measure_page)
    dimension_valid = True
    invalid_dimensions = []

    for dimension in measure_page.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension)
        if not dimension_form.validate():
            invalid_dimensions.append(Dimension(**dimension))

    # Check measure is valid
    if not measure_form.validate() or invalid_dimensions:
        message = 'Cannot submit for review, please see errors below'
        flash(message, 'error')
        if invalid_dimensions:
            for invalid_dimension in invalid_dimensions:
                message = 'Cannot submit for review ' \
                          '<a href="./%s/edit?validate=true">%s</a> dimension is not complete.'\
                          % (invalid_dimension.guid, invalid_dimension.title)
                flash(message, 'error')

        current_status = measure_page.status
        available_actions = measure_page.available_actions()
        if 'APPROVE' in available_actions:
            numerical_status = measure_page.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        context = {
            'form': measure_form,
            'topic': topic_page,
            'subtopic': subtopic_page,
            'measure': measure_page,
            'status': current_status,
            'available_actions': available_actions,
            'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        }

        return render_template("cms/edit_measure_page.html", **context)

    message = 'User %s updated page. ' % current_user.email
    page = page_service.next_state(measure, message)

    build = page.eligible_for_build(current_app.config['BETA_PUBLICATION_STATES'])
    status = page.status.replace('_', ' ').title()
    message = '"{}" sent to {}'.format(page.title, status)
    flash(message, 'info')

    if build:
        return redirect(url_for("cms.edit_measure_page",
                                topic=topic, subtopic=subtopic, measure=measure, build=build))
    else:
        return redirect(url_for("cms.edit_measure_page",
                                topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/reject')
@internal_user_required
@login_required
def reject_page(topic, subtopic, measure):
    message = 'User %s rejected page.' % current_user.email
    page = page_service.reject_page(measure, message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/dimension/new', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_dimension(topic, subtopic, measure):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page(measure)
    except PageNotFoundException:
        abort(404)

    form = DimensionForm()
    if request.method == 'POST':
        form = DimensionForm(request.form)
        messages = []
        if form.validate():
            try:
                dimension = page_service.create_dimension(page=measure_page,
                                                          title=form.data['title'],
                                                          time_period=form.data['time_period'],
                                                          summary=form.data['summary'],
                                                          suppression_rules=form.data['suppression_rules'],
                                                          disclosure_control=form.data['disclosure_control'],
                                                          type_of_statistic=form.data['type_of_statistic'],
                                                          location=form.data['location'],
                                                          source=form.data['source'],
                                                          user=current_user.email
                                                          )
                message = 'Created dimension {}'.format(dimension.title)
                flash(message, 'info')
                return redirect(url_for("cms.edit_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        dimension=dimension.guid))
            except(DimensionAlreadyExists):
                flash('Dimension with code %s already exists' % form.data['title'], 'error')
                return redirect(url_for("cms.create_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        messages=[{'message': 'Dimension with code %s already exists'
                                                              % form.data['title']}]))
        else:
            flash('Please complete all fields in the form', 'error')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page
               }
    return render_template("cms/create_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_dimension(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    validate = request.args.get('validate')
    if validate:
        form = DimensionRequiredForm(obj=dimension)
        if not form.validate():
            message = "Cannot submit for review, please see errors below"
            flash(message, 'error')
    else:
        form = DimensionForm(obj=dimension)

    if request.method == 'POST':
        form = DimensionForm(request.form)
        if form.validate():
            page_service.update_dimension(measure_page=measure_page,
                                          dimension=dimension,
                                          data=form.data)

            message = 'Updated dimension {}'.format(dimension.title)
            flash(message, 'info')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "dimension": dimension
               }
    return render_template("cms/edit_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/create_chart')
@internal_user_required
@login_required
def create_chart(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object,
               'reload_settings': dimension_object.__dict__()['chart_source_data']}

    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/create_table')
@internal_user_required
@login_required
def create_table(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object,
               'reload_settings': dimension_object.__dict__()['table_source_data']}

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_chart', methods=["POST"])
@internal_user_required
@login_required
def save_chart_to_page(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_obj = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    chart_json = request.json

    page_service.update_measure_dimension(measure_page, dimension_obj, chart_json)

    message = 'Chart updated'.format()
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete_chart')
@internal_user_required
@login_required
def delete_chart(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.update_dimension(measure_page=measure_page,
                                  dimension=dimension,
                                  data={'chart': None})
    message = 'Chart deleted'
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            dimension=dimension.guid))


# TODO give this the same treatment as save chart to page
@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_table', methods=["POST"])
@internal_user_required
@login_required
def save_table_to_page(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    table_json = request.json

    page_service.update_measure_dimension(measure_page, dimension_object, table_json)

    message = 'Table updated'.format()
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete_table')
@internal_user_required
@login_required
def delete_table(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    print(dimension.table_source_data)
    page_service.update_dimension(measure_page=measure_page,
                                  dimension=dimension,
                                  data= {'table': {}})
    page_service.save_page(measure_page)

    message = 'Table deleted'
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            dimension=dimension.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/uploads/<upload>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_upload(topic, subtopic, measure, upload):
    try:
        measure_page = page_service.get_page(measure)
    except PageNotFoundException:
        abort(404)

    page_service.delete_upload(measure, upload)
    message = '{} deleted'.format(upload)
    flash(message, 'info')
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/page', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page(topic, subtopic, measure):
    try:
        page = page_service.get_page(measure)
        return page.page_json, 200
    except(PageNotFoundException):
        return json.dumps({}), 404


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/uploads', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page_uploads(topic, subtopic, measure):
    try:
        uploads = page_service.get_page_uploads(measure)
        return json.dumps({'uploads': uploads}), 200
    except PageNotFoundException:
        return json.dumps({}), 404


@internal_user_required
@login_required
@cms_blueprint.route('/build-static-site', methods=['GET'])
def build_static_site():
    from application.sitebuilder.build import do_it
    do_it(current_app)
    return 'OK', 200


def _get_bool(param):
    if param in ['True', '1', 'true', 'yes']:
        return True
    elif param in ['False', '0', 'false', 'no']:
        return False
    return False


def _build_site_if_required(context, page, beta_publication_states):
    build = _get_bool(request.args.get('build'))
    if build and page.eligible_for_build(beta_publication_states):
        context['build'] = build

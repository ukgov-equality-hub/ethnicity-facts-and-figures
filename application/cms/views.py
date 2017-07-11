import io
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
from werkzeug.datastructures import CombinedMultiDict, FileStorage

from application.cms import cms_blueprint
from application.cms.data_utils import Harmoniser

from application.cms.exceptions import (
    PageNotFoundException,
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageExistsException,
    UploadNotFoundException)

from application.cms.forms import (
    MeasurePageForm,
    DimensionForm,
    MeasurePageRequiredForm,
    DimensionRequiredForm,
    UploadForm)

from application.cms.models import publish_status
from application.cms.page_service import page_service
from application.utils import get_bool, internal_user_required


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
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm()
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        try:
            if form.validate():
                page = page_service.create_page(page_type='measure',
                                                parent=subtopic_page.guid,
                                                data=form.data,
                                                user=current_user.email)

                message = 'created page {}'.format(page.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic_page.guid,
                                        subtopic=subtopic_page.guid,
                                        measure=page.guid))
            else:
                flash(form.errors, 'error')
        except PageExistsException:
            message = 'A page with code {} already exists'.format(form.data['guid'])
            flash(message, 'error')
            current_app.logger.error(message)
            return redirect(url_for("cms.create_measure_page",
                                    topic=topic,
                                    subtopic=subtopic))

    return render_template("cms/new_measure_page.html",
                           form=form,
                           topic=topic_page,
                           subtopic=subtopic_page)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/uploads/<upload>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_upload(topic, subtopic, measure, upload):
    try:
        measure_page = page_service.get_page(measure)
        upload_object = measure_page.get_upload(upload)
    except PageNotFoundException:
        abort(404)
        print("MEASURE NOT FOUND")
    except UploadNotFoundException:
        print("UPLOAD NOT FOUND")
        abort(404)
    page_service.delete_upload_obj(measure_page, upload_object.guid)

    message = 'Deleted upload {}'.format(upload_object.title)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/uploads/<upload>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_upload(topic, subtopic, measure, upload):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        upload_obj = measure_page.get_upload(upload)
    except PageNotFoundException:
        abort(404)
    except UploadNotFoundException:
        abort(404)

    form = UploadForm(obj=upload_obj)

    if request.method == 'POST':
        form = UploadForm(request.form)
        if form.validate():
            page_service.edit_measure_upload(measure=measure_page,
                                             upload=upload_obj,
                                             data=form.data)
            message = 'Updated upload {}'.format(upload_obj.title)
            flash(message, 'info')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "upload": upload_obj
               }
    return render_template("cms/edit_upload.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_dimension(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_dimension(measure_page, dimension_object.guid)

    message = 'Deleted dimension {}'.format(dimension_object.title)
    current_app.logger.info(message)
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
            message = 'updated page "{}"'.format(page.guid)
            page_service.update_page(page, data=form.data, message=message)
            current_app.logger.info(message)
            flash(message, 'info')
        else:
            current_app.logger.error('Invalid form')

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

    if page.children and page.subtopics is not None:
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

    if page.children and page.subtopics is not None:
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


# @cms_blueprint.route('/<topic>/<subtopic>/<measure>/upload', methods=['POST'])
# @internal_user_required
# @login_required
# def upload_file(topic, subtopic, measure):
#     file = request.files['file']
#     if file.filename == '':
#         return json.dumps({'status': 'BAD REQUEST'}), 400
#     else:
#         page_service.upload_data(measure, file)
#         return json.dumps({'status': 'OK', 'file': file.filename}), 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/upload', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_upload(topic, subtopic, measure):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page(measure)
    except PageNotFoundException:
        abort(404)

    form = UploadForm()
    if request.method == 'POST':
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data
            page_service.create_upload(page=measure_page,
                                       upload=f,
                                       title=form.data['title'],
                                       description=form.data['description'],
                                       )

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page
               }
    return render_template("cms/create_upload.html", **context)


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

    measure_form = MeasurePageRequiredForm(obj=measure_page)
    dimension_valid = True
    invalid_dimensions = []

    for dimension in measure_page.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension)
        if not dimension_form.validate():
            invalid_dimensions.append(dimension)

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

    message = page_service.next_state(measure_page)
    flash(message, 'info')

    build = measure_page.eligible_for_build(current_app.config['BETA_PUBLICATION_STATES'])
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
    measure_page = page_service.get_page(measure)
    message = page_service.reject_page(measure_page)
    flash(message, 'info')
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
                                                          source=form.data['source'])
                message = 'Created dimension "{}"'.format(dimension.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        dimension=dimension.guid))
            except(DimensionAlreadyExists):
                message = 'Dimension with title "{}" already exists'.format(form.data['title'])
                flash(message, 'error')
                current_app.logger.error(message)
                return redirect(url_for("cms.create_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        messages=[{'message': 'Dimension with code %s already exists'
                                                              % form.data['title']}]))
        else:
            flash('Please complete all fields in the form', 'error')

    context = {"form": form,
               "create": True,
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
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        print("DIMENSION NOT FOUND")
        abort(404)

    validate = request.args.get('validate')
    if validate:
        form = DimensionRequiredForm(obj=dimension_object)
        if not form.validate():
            message = "Cannot submit for review, please see errors below"
            flash(message, 'error')
    else:
        form = DimensionForm(obj=dimension_object)

    if request.method == 'POST':
        form = DimensionForm(request.form)
        if form.validate():
            page_service.update_dimension(dimension=dimension_object,
                                          data=form.data)
            message = 'Updated dimension {}'.format(dimension)
            flash(message, 'info')

    context = {"form": form,
               "create": False,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "dimension": dimension_object
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
               'dimension': dimension_object.to_dict(),
               'simple_chart_builder': current_app.config['SIMPLE_CHART_BUILDER']}

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
               'dimension': dimension_object.to_dict()}

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_chart', methods=["POST"])
@internal_user_required
@login_required
def save_chart_to_page(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    chart_json = request.json

    page_service.update_measure_dimension(measure_page, dimension_object, chart_json)
    stream = io.BytesIO(chart_json['rawData'].encode('utf-8'))
    filename = '%s.csv' % dimension_object.guid
    file = FileStorage(stream=stream, filename=filename)
    page_service.upload_data(measure_page.guid, file, upload_type='chart')

    message = 'updated chart on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete_chart')
@internal_user_required
@login_required
def delete_chart(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_chart(dimension_object)

    message = 'deleted chart from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            dimension=dimension_object.guid))


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

    stream = io.BytesIO(table_json['rawData'].encode('utf-8'))
    filename = '%s.csv' % dimension_object.guid
    file = FileStorage(stream=stream, filename=filename)
    page_service.upload_data(measure_page.guid, file, upload_type='table')

    message = 'updated table on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/delete_table')
@internal_user_required
@login_required
def delete_table(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_table(dimension=dimension_object)

    message = 'deleted table from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            dimension=dimension_object.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/page', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page(topic, subtopic, measure):
    try:
        page = page_service.get_page(measure)
        return page.page_json, 200
    except PageNotFoundException:
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


def _build_site_if_required(context, page, beta_publication_states):
    build = get_bool(request.args.get('build'))
    if build and page.eligible_for_build(beta_publication_states):
        context['build'] = build


@cms_blueprint.route('/data_processor', methods=['POST'])
@internal_user_required
@login_required
def process_input_data():
    if current_app.config['HARMONISER_ENABLED']:
        request_json = request.json
        return_data = Harmoniser(current_app.config['HARMONISER_FILE']).process_data(request_json['data'])
        return json.dumps({'data': return_data}), 200
    else:
        return json.dumps(request.json), 200

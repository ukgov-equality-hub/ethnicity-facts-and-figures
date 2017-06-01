import json

from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash,
    current_app,
    jsonify)

from flask_login import login_required

from application.cms import cms_blueprint
from application.cms.utils import internal_user_required
from application.cms.forms import PageForm, MeasurePageForm, DimensionForm
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException, DimensionAlreadyExists
from application.cms.exceptions import PageExistsException
from application.cms.models import publish_status
from application.cms.page_service import page_service


@cms_blueprint.route('/')
@internal_user_required
@login_required
def index():
    pages = page_service.get_pages()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/topic/new', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_topic_page():

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page = page_service.create_page(page_type='topic', data=form.data)
            message = 'Created page {}'.format(page.title)
            flash(message, 'info')
            return redirect(url_for("cms.edit_topic_page", slug=page.meta.uri))
    return render_template("cms/new_topic_page.html", form=form)


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
                page = page_service.create_page(page_type='measure', parent=subtopic_page.meta.guid, data=form.data)
                message = 'Created page {}'.format(page.title)
                flash(message, 'info')
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic_page.meta.guid,
                                        subtopic=subtopic_page.meta.guid,
                                        measure=page.meta.guid))
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


@cms_blueprint.route('/<topic>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_topic_page(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    form = PageForm(obj=page)
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page_service.update_page(page, data=form.data)
            message = 'Updated page {}'.format(page.title)
            flash(message, 'info')

    current_status = page.meta.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status + 1]

    context = {
        'form': form,
        'slug': topic,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None
    }

    return render_template("cms/edit_topic_page.html", **context)


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
            page_service.update_page(page, data=form.data)
            message = 'Updated page {}'.format(page.title)
            flash(message, 'info')
        else:
            print("NOT VALIDATED")
            print(form.errors)

    current_status = page.meta.status
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
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None
    }

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic_overview(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    pages = page_service.get_pages()
    topic_page = [p for p in pages if str(p) == page.guid][0]
    children = pages[topic_page]

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

    pages = page_service.get_pages()
    for item in pages.items():
        subtopics = item[1]
        try:
            subtopic_page = [p for p in subtopics if str(p) == page.guid][0]
            children = pages[item[0]][subtopic_page]
            topic_page = item[0]
        except IndexError:
            pass

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
        page_service.upload_data(page, file)
        return json.dumps({'status': 'OK', 'file': file.filename}), 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/publish', methods=['GET', 'POST'])
@internal_user_required
@login_required
def publish_page(topic, subtopic, measure):
    page = page_service.next_state(measure)
    status = page.meta.status.replace('_', ' ').title()
    message = '"{}" sent to {}'.format(page.title, status)
    flash(message, 'info')
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/reject')
@internal_user_required
@login_required
def reject_page(topic, subtopic, measure):
    page = page_service.reject_page(measure)
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
                                                          summary=form.data['summary'])
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
        dimension = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)
    form = DimensionForm(obj=dimension)
    if request.method == 'POST':
        form = DimensionForm(request.form)
        if form.validate():
            page_service.update_dimension(page=measure_page, dimension=dimension, data=form.data)
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
        dimension_object = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object,
               'reload_settings': page_service.reload_dimension_source_data('chart.json', measure, dimension)}

    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/create_table')
@internal_user_required
@login_required
def create_table(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object,
               'reload_settings': page_service.reload_dimension_source_data('table.json', measure, dimension)}

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_chart', methods=["POST"])
@internal_user_required
@login_required
def save_chart_to_page(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    chart_json = request.json

    try:
        page_service.get_dimension(measure_page, dimension.guid)
    except DimensionNotFoundException:
        page_service.create_dimension(page=measure_page, title=dimension)

    page_service.update_dimension(measure_page, dimension, {'chart': chart_json['chartObject']})
    page_service.update_dimension_source_data('chart.json', measure_page, dimension.guid, chart_json['source'])
    page_service.save_page(measure_page)

    message = 'Chart updated'.format()
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_table', methods=["POST"])
@internal_user_required
@login_required
def save_table_to_page(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension = page_service.get_dimension(measure_page, dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    table_json = request.json

    try:
        page_service.get_dimension(measure_page, dimension.guid)
    except DimensionNotFoundException:
        page_service.create_dimension(page=measure_page, title=dimension)

    page_service.update_dimension(measure_page, dimension, {'table': table_json['tableObject']})
    page_service.update_dimension_source_data('table.json', measure_page, dimension.guid, table_json['source'])
    page_service.save_page(measure_page)

    message = 'Table updated'.format()
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/page', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page(topic, subtopic, measure):
    try:
        page = page_service.get_page(measure)
        return page.to_json(), 200
    except(PageNotFoundException):
        return json.dumps({}), 404

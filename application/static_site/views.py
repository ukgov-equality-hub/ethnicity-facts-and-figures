import csv
from io import StringIO

from botocore.exceptions import ClientError

from flask import (
    render_template,
    abort,
    current_app,
    make_response,
    jsonify)

from flask_security import login_required

from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException
from application.utils import internal_user_required
from flask_security import current_user

from application.static_site import static_site_blueprint
from application.cms.page_service import page_service

from os.path import split


@static_site_blueprint.route('/')
@internal_user_required
@login_required
def index():
    return render_template('static_site/index.html')


@static_site_blueprint.route('/about-ethnicity')
@internal_user_required
@login_required
def about_ethnicity():
    return render_template('static_site/about_ethnicity.html')


@static_site_blueprint.route('/ethnic-groups-and-data-collected')
@internal_user_required
@login_required
def ethnic_groups_and_data_collected():
    return render_template('static_site/ethnic_groups_and_data_collected.html')


@static_site_blueprint.route('/background')
@internal_user_required
@login_required
def background():
    return render_template('static_site/background.html')


@static_site_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic(topic):
    guid = 'topic_%s' % topic.replace('-', '')
    approval_states = current_app.config['BETA_PUBLICATION_STATES']
    try:
        page = page_service.get_page(guid)
    except PageNotFoundException:
        abort(404)
    subtopics = []
    if page.children:
        ordered_subtopics = []
        for st in page.subtopics:
            for s in page.children:
                if s.guid == st:
                    ordered_subtopics.append(s)
        subtopics = ordered_subtopics
    return render_template('static_site/topic.html',
                           page=page,
                           subtopics=subtopics,
                           approval_states=approval_states)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>.json')
def measure_page_json(topic, subtopic, measure):
    subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
    try:
        page = page_service.get_page_by_uri(subtopic_guid, measure)
    except PageNotFoundException:
        abort(404)
    # create the dict form of measure page and return it
    return jsonify(page.to_dict())


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>')
@login_required
def measure_page(topic, subtopic, measure):
        subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
        try:
            page = page_service.get_page_by_uri(subtopic_guid, measure)
        except PageNotFoundException:
            abort(404)
        if current_user.is_departmental_user():
            if page.status not in ['DEPARTMENT_REVIEW', 'ACCEPTED']:
                return render_template('static_site/not_ready_for_review.html')
        uploads = page_service.get_page_uploads(page.guid)
        dimensions = [dimension.to_dict() for dimension in page.dimensions]
        return render_template('static_site/measure.html',
                               topic=topic,
                               subtopic=subtopic,
                               measure_page=page,
                               dimensions=dimensions)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>/downloads/<filename>')
@login_required
def measure_page_file_download(topic, subtopic, measure, filename):
    try:
        upload_obj = page_service.get_upload(measure, filename)
        file_contents = page_service.get_measure_download(upload_obj, filename, 'data')
        response = make_response(file_contents)

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % upload_obj.file_name
        return response
    except (FileNotFoundError, ClientError) as e:
        abort(404)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>/dimension/<dimension>/download')
@login_required
def dimension_file_download(topic, subtopic, measure, dimension):
    try:
        measure_page = page_service.get_page(measure)
        dimension_obj = measure_page.get_dimension(dimension)

        data = write_dimension_csv(dimension_obj, current_app.config['RDU_SITE'])
        response = make_response(data)

        if dimension_obj.title:
            filename = '%s.csv' % dimension_obj.title.lower().replace(' ', '_').replace(',', '')
        else:
            filename = '%s.csv' % dimension_obj.guid

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException as e:
        abort(404)


def write_dimension_csv(dimension, source):

    source_data = dimension.table_source_data if dimension.table else dimension.chart_source_data

    metadata = [['Title', dimension.title],
                ['Location', dimension.location],
                ['Time period', dimension.time_period],
                ['Data source', dimension.source],
                ['Source', source]
                ]

    csv_columns = source_data['data'][0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('')
        writer.writerow(csv_columns)
        for row in source_data['data'][1:]:
            writer.writerow(row)

        return output.getvalue()

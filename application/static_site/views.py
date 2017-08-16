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


@static_site_blueprint.route('/ethnicity_and_type_of_family_or_household')
@internal_user_required
@login_required
def ethnicity_and_type_of_family_or_household():
    return render_template('static_site/ethnicity_and_type_of_family_or_household.html')


@static_site_blueprint.route('/ethnic_groups_by_gender')
@internal_user_required
@login_required
def ethnic_groups_by_gender():
    return render_template('static_site/ethnic_groups_by_gender.html')


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

    measures = {}
    for st in subtopics:
        ms = page_service.get_latest_measures(st)
        measures[st.guid] = ms

    return render_template('static_site/topic.html',
                           page=page,
                           subtopics=subtopics,
                           measures=measures)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/data.json')
def measure_page_json(topic, subtopic, measure, version):
    subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
    try:
        page = page_service.get_page_by_uri(subtopic_guid, measure, version)
    except PageNotFoundException:
        abort(404)
    # create the dict form of measure page and return it
    return jsonify(page.to_dict())


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>')
@login_required
def measure_page(topic, subtopic, measure, version):
        subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
        try:
            if version == 'latest':
                page = page_service.get_latest_version(subtopic_guid, measure)
            else:
                page = page_service.get_page_by_uri(subtopic_guid, measure, version)
        except PageNotFoundException:
            abort(404)
        if current_user.is_departmental_user():
            if page.status not in ['DEPARTMENT_REVIEW', 'APPROVED']:
                return render_template('static_site/not_ready_for_review.html')

        versions = page_service.get_previous_versions(page)
        dimensions = [dimension.to_dict() for dimension in page.dimensions]
        return render_template('static_site/measure.html',
                               topic=topic,
                               subtopic=subtopic,
                               measure_page=page,
                               dimensions=dimensions,
                               versions=versions)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/downloads/<filename>')
@login_required
def measure_page_file_download(topic, subtopic, measure, version, filename):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        upload_obj = page_service.get_upload(measure, version, filename)
        file_contents = page_service.get_measure_download(upload_obj, filename, 'data')
        meta_data = "Title, %s\nTime period, %s\nLocation, %s\nSource, %s\nDepartment, %s\nLast update, %s" \
                    % (measure_page.title,
                       measure_page.time_covered,
                       measure_page.geographic_coverage,
                       measure_page.source_text,
                       measure_page.department_source,
                       measure_page.last_update_date)
        file_contents = file_contents.splitlines()[6:]
        response_file_content = meta_data.encode('utf-8')
        for line in file_contents:
            response_file_content += '\n'.encode('utf-8') + line

        response = make_response(response_file_content)
        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % upload_obj.file_name
        return response
    except (FileNotFoundError, ClientError) as e:
        abort(404)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/dimension/<dimension>/download')
@login_required
def dimension_file_download(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_obj = measure_page.get_dimension(dimension)

        data = write_dimension_csv(dimension=dimension_obj,
                                   source=current_app.config['RDU_SITE'],
                                   location=measure_page.geographic_coverage,
                                   time_period=measure_page.time_covered,
                                   data_source="%s %s" %(measure_page.source_text, measure_page.source_url))
        response = make_response(data)

        if dimension_obj.title:
            filename = '%s.csv' % dimension_obj.title.lower().replace(' ', '_').replace(',', '')
        else:
            filename = '%s.csv' % dimension_obj.guid

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException as e:
        abort(404)


def write_dimension_csv(dimension, source, location, time_period, data_source):
    source_data = dimension.table_source_data if dimension.table else dimension.chart_source_data

    metadata = [['Title', dimension.title],
                ['Location', location],
                ['Time period', time_period],
                ['Data source', data_source],
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

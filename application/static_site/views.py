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

from application.cms.data_utils import DimensionObjectBuilder
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


@static_site_blueprint.route('/about-ethnicity/population-by-ethnicity')
@internal_user_required
@login_required
def population_by_ethnicity():
    return render_template('static_site/population_by_ethnicity.html')


@static_site_blueprint.route('/about-ethnicity/ethnicity-and-type-of-family-or-household')
@internal_user_required
@login_required
def ethnicity_and_type_of_family_or_household():
    return render_template('static_site/ethnicity_and_type_of_family_or_household.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-by-age')
@internal_user_required
@login_required
def ethnic_groups_by_age():
    return render_template('static_site/ethnic_groups_by_age.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-by-gender')
@internal_user_required
@login_required
def ethnic_groups_by_gender():
    return render_template('static_site/ethnic_groups_by_gender.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-by-economic-status')
@internal_user_required
@login_required
def ethnic_groups_by_economic_status():
    return render_template('static_site/ethnic_groups_by_economic_status.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-by-sexual-identity')
@internal_user_required
@login_required
def ethnic_groups_by_sexual_identity():
    return render_template('static_site/ethnic_groups_by_sexual_identity.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-and-data-collected')
@internal_user_required
@login_required
def ethnic_groups_and_data_collected():
    return render_template('static_site/ethnic_groups_and_data_collected.html')


@static_site_blueprint.route('/about-ethnicity/ethnic-groups-by-place-of-birth')
@internal_user_required
@login_required
def ethnic_groups_by_place_of_birth():
    return render_template('static_site/ethnic_groups_by_place_of_birth.html')


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
        edit_history = page_service.get_previous_edits(page)
        first_published_date = page_service.get_first_published_date(page)

        newer_edition = page_service.get_latest_version_of_newer_edition(page)

        dimensions = [dimension.to_dict() for dimension in page.dimensions]
        return render_template('static_site/measure.html',
                               topic=topic,
                               subtopic=subtopic,
                               measure_page=page,
                               dimensions=dimensions,
                               versions=versions,
                               first_published_date=first_published_date,
                               newer_edition=newer_edition,
                               edit_history=edit_history)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/downloads/<filename>')
@login_required
def measure_page_file_download(topic, subtopic, measure, version, filename):
    try:
        page = page_service.get_page_with_version(measure, version)
        upload_obj = page_service.get_upload(measure, version, filename)
        file_contents = page_service.get_measure_download(upload_obj, filename, 'source')
        meta_data = "Title, %s\nTime period, %s\nLocation, %s\nSource, %s\nDepartment, %s\nLast update, %s\n" \
                    % (page.title,
                       page.time_covered,
                       page.geographic_coverage,
                       page.source_text,
                       page.department_source,
                       page.last_update_date)

        response_file_content = meta_data.encode('utf-8')
        file_contents = file_contents.splitlines()

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
        page = page_service.get_page_with_version(measure, version)
        # dimension_obj =  page.get_dimension(dimension)
        dimension_obj =  DimensionObjectBuilder.build(page.get_dimension(dimension))

        data = write_dimension_csv(dimension=dimension_obj)
        response = make_response(data)

        if dimension_obj['context']['dimension'] and dimension_obj['context']['dimension'] != '':
            filename = '%s.csv' % dimension_obj['context']['dimension'].lower().replace(' ', '_').replace(',', '')
        else:
            filename = '%s.csv' % dimension_obj['context']['guid']

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException as e:
        abort(404)


def write_dimension_csv(dimension):
    if 'table' in dimension:
        source_data = dimension['table']['data']
    elif 'chart' in dimension:
        source_data = dimension['chart']['data']
    else:
        source_data = [[]]

    metadata = [['Title', dimension['context']['dimension']],
                ['Location', dimension['context']['location']],
                ['Time period', dimension['context']['time_period']],
                ['Data source', dimension['context']['department']],
                ['Source', "%s %s" % (dimension['context']['source_text'], dimension['context']['source_url'])]
                ]

    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('')
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()

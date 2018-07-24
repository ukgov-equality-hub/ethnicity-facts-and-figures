import os
from tempfile import NamedTemporaryFile

from botocore.exceptions import ClientError
from flask import (
    render_template,
    abort,
    make_response,
    jsonify,
    send_file,
    request)

from flask_security import current_user
from flask_security import login_required
from slugify import slugify

from application.cms.data_utils import DimensionObjectBuilder
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException, UploadNotFoundException
from application.cms.models import Page
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.static_site import static_site_blueprint
from application.utils import (
    get_content_with_metadata,
    write_dimension_csv,
    write_dimension_tabular_csv,
    user_has_access
)

from application.dashboard.data_helpers import (
    get_published_dashboard_data_by_year_and_month
)


from application.cms.api_builder import build_index_json, build_measure_json


@static_site_blueprint.route('/')
@login_required
def index():
    topics = Page.query.filter_by(page_type='topic', parent_guid='homepage').order_by(Page.title.asc()).all()
    return render_template('static_site/index.html', topics=topics, static_mode=request.args.get('static_mode', False))


@static_site_blueprint.route('/whats-new')
@login_required
def whats_new():
    months = get_published_dashboard_data_by_year_and_month()
    return render_template('static_site/whats_new.html', months=months)


@static_site_blueprint.route('/ethnicity-in-the-uk')
@login_required
def ethnicity_in_the_uk():
    return render_template('static_site/static_pages/ethnicity_in_the_uk.html')


@static_site_blueprint.route('/ethnicity-in-the-uk/<file>')
@login_required
def ethnicity_in_the_uk_page(file):
    f = file.replace('-', '_')
    return render_template('static_site/static_pages/ethnicity_in_the_uk/%s.html' % f)


@static_site_blueprint.route('/background')
@login_required
def background():
    return render_template('static_site/static_pages/background.html')


@static_site_blueprint.route('/cookies')
@login_required
def cookies():
    return render_template('static_site/static_pages/cookies.html')


@static_site_blueprint.route('/privacy-policy')
@login_required
def privacy_policy():
    return render_template('static_site/static_pages/privacy-policy.html')


@static_site_blueprint.route('/<uri>')
@login_required
def topic(uri):
    try:
        topic = page_service.get_page_by_uri_and_type(uri, 'topic')
    except PageNotFoundException:
        abort(404)
    measures = {}

    for st in topic.children:
        ms = page_service.get_latest_measures(st)
        measures[st.guid] = ms

    return render_template('static_site/topic.html',
                           topic=topic,
                           subtopics=topic.children,
                           measures=measures,
                           static_mode=request.args.get('static_mode', False))


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/data.json')
@user_has_access
def measure_page_json(topic, subtopic, measure, version):
    subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')

    try:
        if version == 'latest':
            page = page_service.get_latest_version(subtopic_guid, measure)
        else:
            page = page_service.get_page_by_uri_and_version(subtopic_guid, measure, version)
    except PageNotFoundException:
        abort(404)

    return jsonify(build_measure_json(page))


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/export')
@login_required
@user_has_access
def measure_page_markdown(topic, subtopic, measure, version):

    subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
    try:
        if version == 'latest':
            page = page_service.get_latest_version(subtopic_guid, measure)
        else:
            page = page_service.get_page_by_uri_and_version(subtopic_guid, measure, version)
    except PageNotFoundException:
        abort(404)
    if current_user.is_departmental_user():
        if page.status not in ['DEPARTMENT_REVIEW', 'APPROVED']:
            return render_template('static_site/not_ready_for_review.html')

    dimensions = [dimension.to_dict() for dimension in page.dimensions]
    return render_template('static_site/export/measure_export.html',
                           topic=topic,
                           subtopic=subtopic,
                           measure_page=page,
                           dimensions=dimensions)


@static_site_blueprint.route('/data.json')
def index_page_json():
    return jsonify(build_index_json())


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>')
@login_required
@user_has_access
def measure_page(topic, subtopic, measure, version):

    subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
    try:
        if version == 'latest':
            page = page_service.get_latest_version(subtopic_guid, measure)
        else:
            page = page_service.get_page_by_uri_and_version(subtopic_guid, measure, version)
    except PageNotFoundException:
        abort(404)

    versions = page_service.get_previous_major_versions(page)
    edit_history = page_service.get_previous_minor_versions(page)
    if edit_history:
        first_published_date = page_service.get_first_published_date(page)
    else:
        first_published_date = page.publication_date

    dimensions = [dimension.to_dict() for dimension in page.dimensions]

    return render_template('static_site/measure.html',
                           topic=topic,
                           subtopic=subtopic,
                           measure_page=page,
                           dimensions=dimensions,
                           versions=versions,
                           first_published_date=first_published_date,
                           edit_history=edit_history,
                           static_mode=request.args.get('static_mode', False))


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/downloads/<filename>')
def measure_page_file_download(topic, subtopic, measure, version, filename):
    try:
        page = page_service.get_page_with_version(measure, version)
        upload_obj = upload_service.get_upload(page, filename)
        downloaded_file = upload_service.get_measure_download(upload_obj, filename, 'source')
        content_with_metadata = get_content_with_metadata(downloaded_file, page)
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if content_with_metadata.strip() == '':
            abort(404)

        outfile = NamedTemporaryFile('w', encoding='windows-1252', delete=False)
        outfile.write(content_with_metadata)
        outfile.flush()

        return send_file(outfile.name, as_attachment=True, mimetype='text/plain', attachment_filename=filename)

    except (UploadNotFoundException, FileNotFoundError, ClientError) as e:
        abort(404)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/dimension/<dimension>/download')
def dimension_file_download(topic, subtopic, measure, version, dimension):
    try:
        page = page_service.get_page_with_version(measure, version)
        dimension_obj = DimensionObjectBuilder.build(page.get_dimension(dimension))

        data = write_dimension_csv(dimension=dimension_obj)
        response = make_response(data)

        if dimension_obj['context']['dimension'] and dimension_obj['context']['dimension'] != '':
            filename = '%s.csv' % cleanup_filename(dimension_obj['context']['dimension'])
        else:
            filename = '%s.csv' % cleanup_filename(dimension_obj['context']['guid'])

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException as e:
        abort(404)


@static_site_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/dimension/<dimension>/tabular-download')
def dimension_file_table_download(topic, subtopic, measure, version, dimension):
    try:
        page = page_service.get_page_with_version(measure, version)
        dimension_obj = DimensionObjectBuilder.build(page.get_dimension(dimension))

        data = write_dimension_tabular_csv(dimension=dimension_obj)
        response = make_response(data)

        if dimension_obj['context']['dimension'] and dimension_obj['context']['dimension'] != '':
            filename = '%s-table.csv' % cleanup_filename(dimension_obj['context']['dimension'].lower())
        else:
            filename = '%s-table.csv' % cleanup_filename(dimension_obj['context']['guid'])

        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException as e:
        abort(404)


def cleanup_filename(filename):
    return slugify(filename)

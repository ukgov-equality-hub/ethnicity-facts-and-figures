from botocore.exceptions import ClientError

from flask import (
    render_template,
    abort,
    send_from_directory,
    current_app,
    make_response
)

from flask_security import login_required

from application.cms.exceptions import PageNotFoundException
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
    return render_template('static_site/topic.html', page=page, subtopics=subtopics)


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

    path = page_service.get_url_for_file(measure, filename)
    directory, file = split(path)
    return send_from_directory(directory=directory, filename=file)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>/dimension/<dimension>/downloads/<filename>')
@login_required
def dimension_file_download(topic, subtopic, measure, dimension, filename):
    try:
        dimension_object = page_service.get_dimension(measure, dimension)
        file_dir = 'table' if dimension_object.table else 'chart'
        file_contents = page_service.get_dimension_download(dimension_object,
                                                            filename, 'dimension/%s' % file_dir,
                                                            current_app.config['RDU_SITE'])
        response = make_response(file_contents)
        file = '%s.csv' % dimension_object.title.lower().replace(' ', '_').replace(',', '')
        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % file
        return response
    except (FileNotFoundError, ClientError) as e:
        abort(404)

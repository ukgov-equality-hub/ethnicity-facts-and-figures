from flask import (
    render_template,
    abort
)

from flask_security import login_required
from application.cms.utils import internal_user_required
from flask_security import current_user

from application.static_site import static_site_blueprint
from application.cms.page_service import page_service


@static_site_blueprint.route('/')
@internal_user_required
@login_required
def index():
    return render_template('static_site/index.html')


@static_site_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic(topic):
    guid = 'topic_%s' % topic.replace('-', '')
    page = page_service.get_page(guid)
    subtopics = page_service.get_subtopics(page)
    return render_template('static_site/topic.html', page=page, subtopics=subtopics)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>')
@login_required
def measure_page(topic, subtopic, measure):
        subtopic_guid = 'subtopic_%s' % subtopic.replace('-', '')
        measure_guid = page_service.get_measure_guid(subtopic_guid, measure)
        if measure_guid is None:
            abort(404)
        measure_page = page_service.get_page(measure_guid)

        if current_user.is_departmental_user():
            if measure_page.meta.status not in ['DEPARTMENT_REVIEW', 'ACCEPTED']:
                return render_template('static_site/not_ready_for_review.html')
        dimensions = [d.__dict__() for d in measure_page.dimensions]
        print("RENDERING MEASURE PAGE")
        print(dimensions[0]["table"])
        return render_template('static_site/measure.html',
                               topic=topic,
                               measure_page=measure_page,
                               dimensions=dimensions)


@static_site_blueprint.route('/about-ethnicity')
@internal_user_required
@login_required
def about_ethnicity():
    return render_template('static_site/about_ethnicity.html')


@static_site_blueprint.route('/background')
@internal_user_required
@login_required
def background():
    return render_template('static_site/background.html')

from flask import render_template
from flask_login import login_required

from application.dashboard import dashboard_blueprint
from application.dashboard.data_helpers import (
    get_published_dashboard_data, get_ethnic_groups_dashboard_data, get_ethnic_group_by_uri_dashboard_data,
    get_ethnicity_categorisations_dashboard_data, get_ethnicity_categorisation_by_id_dashboard_data,
    get_geographic_breakdown_dashboard_data, get_geographic_breakdown_by_slug_dashboard_data,
    get_measure_progress_dashboard_data)
from application.factory import page_service
from application.utils import internal_user_required


@dashboard_blueprint.route('/')
@internal_user_required
@login_required
def index():
    return render_template('dashboards/index.html')


@dashboard_blueprint.route('/published')
@internal_user_required
@login_required
def published():
    data = get_published_dashboard_data()
    return render_template('dashboards/publications.html', data=data)


@dashboard_blueprint.route('/measures')
@internal_user_required
@login_required
def measures_list():
    pages = page_service.get_pages_by_type('topic')
    return render_template('dashboards/measures.html', pages=pages)


@dashboard_blueprint.route('/measure-progress')
@internal_user_required
@login_required
def measure_progress():
    measures, planned_count, progress_count, review_count = get_measure_progress_dashboard_data()
    return render_template('dashboards/measure_progress.html',
                           measures=measures,
                           planned_count=planned_count,
                           progress_count=progress_count,
                           review_count=review_count,
                           )


@dashboard_blueprint.route('/ethnic-groups')
@internal_user_required
@login_required
def ethnic_groups():
    sorted_ethnicity_list = get_ethnic_groups_dashboard_data()
    return render_template('dashboards/ethnicity_values.html', ethnic_groups=sorted_ethnicity_list)


@dashboard_blueprint.route('/ethnic-groups/<value_uri>')
@internal_user_required
@login_required
def ethnic_group(value_uri):
    value_title, page_count, results = get_ethnic_group_by_uri_dashboard_data(value_uri)
    return render_template('dashboards/ethnic_group.html',
                           ethnic_group=value_title,
                           measure_count=page_count,
                           measure_tree=results,
                           )


@dashboard_blueprint.route('/ethnicity-categorisations')
@internal_user_required
@login_required
def ethnicity_categorisations():
    categorisations = get_ethnicity_categorisations_dashboard_data()
    return render_template('dashboards/ethnicity_categorisations.html',
                           ethnicity_categorisations=categorisations)


@dashboard_blueprint.route('/ethnicity-categorisations/<categorisation_id>')
@internal_user_required
@login_required
def ethnicity_categorisation(categorisation_id):
    categorisation_title, page_count, results = get_ethnicity_categorisation_by_id_dashboard_data(categorisation_id)
    return render_template('dashboards/ethnicity_categorisation.html',
                           categorisation_title=categorisation_title,
                           page_count=page_count,
                           measure_tree=results,
                           )


@dashboard_blueprint.route('/geographic-breakdown')
@internal_user_required
@login_required
def locations():
    location_levels = get_geographic_breakdown_dashboard_data()
    return render_template('dashboards/geographic-breakdown.html',
                           location_levels=location_levels)


@dashboard_blueprint.route('/geographic-breakdown/<slug>')
@internal_user_required
@login_required
def location(slug):
    loc, page_count, subtopics = get_geographic_breakdown_by_slug_dashboard_data(slug)
    return render_template('dashboards/lowest-level-of-geography.html',
                           level_of_geography=loc.name,
                           page_count=page_count,
                           measure_tree=subtopics,
                           )

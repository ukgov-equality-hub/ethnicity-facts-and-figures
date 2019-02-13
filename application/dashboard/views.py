from flask import render_template
from flask_login import login_required

from application.auth.models import VIEW_DASHBOARDS
from application.dashboard import dashboard_blueprint

from application.dashboard.data_helpers import (
    get_published_dashboard_data,
    get_ethnic_groups_dashboard_data,
    get_ethnic_group_by_slug_dashboard_data,
    get_ethnicity_classifications_dashboard_data,
    get_ethnicity_classification_by_id_dashboard_data,
    get_geographic_breakdown_dashboard_data,
    get_geographic_breakdown_by_slug_dashboard_data,
    get_planned_pages_dashboard_data,
    get_published_measures_by_years_and_months,
)

from application.factory import new_page_service
from application.utils import user_can


@dashboard_blueprint.route("")
@login_required
@user_can(VIEW_DASHBOARDS)
def index():
    return render_template("dashboards/index.html")


@dashboard_blueprint.route("/whats-new")
@login_required
def whats_new():
    pages_by_years_and_months = get_published_measures_by_years_and_months()
    return render_template("dashboards/whats_new.html", pages_by_years_and_months=pages_by_years_and_months)


@dashboard_blueprint.route("/published")
@login_required
@user_can(VIEW_DASHBOARDS)
def published():
    data = get_published_dashboard_data()
    return render_template("dashboards/publications.html", data=data)


@dashboard_blueprint.route("/measures")
@login_required
@user_can(VIEW_DASHBOARDS)
def measures_list():
    topics = new_page_service.get_all_topics()
    return render_template("dashboards/measures.html", topics=topics)


@dashboard_blueprint.route("/planned-pages")
@login_required
@user_can(VIEW_DASHBOARDS)
def planned_pages():
    measures, planned_count, progress_count, review_count = get_planned_pages_dashboard_data()
    return render_template(
        "dashboards/planned_pages.html",
        measures=measures,
        planned_count=planned_count,
        progress_count=progress_count,
        review_count=review_count,
    )


@dashboard_blueprint.route("/ethnic-groups")
@login_required
@user_can(VIEW_DASHBOARDS)
def ethnic_groups():
    sorted_ethnicity_list = get_ethnic_groups_dashboard_data()
    return render_template("dashboards/ethnicity_values.html", ethnic_groups=sorted_ethnicity_list)


@dashboard_blueprint.route("/ethnic-groups/<value_slug>")
@login_required
@user_can(VIEW_DASHBOARDS)
def ethnic_group(value_slug):
    value_title, page_count, nested_measures_and_dimensions = get_ethnic_group_by_slug_dashboard_data(value_slug)
    return render_template(
        "dashboards/ethnic_group.html",
        ethnic_group=value_title,
        measure_count=page_count,
        nested_measures_and_dimensions=nested_measures_and_dimensions,
    )


@dashboard_blueprint.route("/ethnicity-classifications")
@login_required
@user_can(VIEW_DASHBOARDS)
def ethnicity_classifications():
    classifications = get_ethnicity_classifications_dashboard_data()
    return render_template("dashboards/ethnicity_classifications.html", ethnicity_classifications=classifications)


@dashboard_blueprint.route("/ethnicity-classifications/<classification_id>")
@login_required
@user_can(VIEW_DASHBOARDS)
def ethnicity_classification(classification_id):
    classification_title, page_count, nested_measures_and_dimensions = get_ethnicity_classification_by_id_dashboard_data(  # noqa
        classification_id
    )
    return render_template(
        "dashboards/ethnicity_classification.html",
        classification_title=classification_title,
        page_count=page_count,
        nested_measures_and_dimensions=nested_measures_and_dimensions,
    )


@dashboard_blueprint.route("/geographic-breakdown")
@login_required
@user_can(VIEW_DASHBOARDS)
def locations():
    location_levels = get_geographic_breakdown_dashboard_data()
    return render_template("dashboards/geographic-breakdown.html", location_levels=location_levels)


@dashboard_blueprint.route("/geographic-breakdown/<slug>")
@login_required
@user_can(VIEW_DASHBOARDS)
def location(slug):
    geography, page_count, measure_titles_and_urls_by_topic_and_subtopic = get_geographic_breakdown_by_slug_dashboard_data(  # noqa
        slug
    )
    return render_template(
        "dashboards/lowest-level-of-geography.html",
        level_of_geography=geography.name,
        page_count=page_count,
        measure_titles_and_urls_by_topic_and_subtopic=measure_titles_and_urls_by_topic_and_subtopic,
    )

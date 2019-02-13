import calendar
from collections import defaultdict
from datetime import date, timedelta

from flask import url_for
from slugify import slugify
from sqlalchemy import func
from trello.exceptions import TokenError

from application.cms.classification_service import classification_service
from application.cms.models import MeasureVersion, LowestLevelOfGeography
from application.dashboard.trello_service import trello_service

# We import everything from application.dashboard.models locally where needed.
# This prevents Alembic from discovering the models and trying to create the
# materialized views as tables, eg when creating a migration or using create_all()
# in test setup.


def get_published_measures_by_years_and_months():
    all_publications = (
        MeasureVersion.published_major_versions()
        .order_by(MeasureVersion.published_at.desc(), MeasureVersion.title)
        .all()
    )

    # Dict of years to dicts of months to lists of pages published that month.
    # dict[year: int] -> dict[published_at_to_month_precision: datetime] -> pages: list
    published_measures_by_years_and_months = defaultdict(lambda: defaultdict(list))

    for publication in all_publications:
        published_measures_by_years_and_months[publication.published_at.year][
            publication.published_at.replace(day=1)
        ].append(publication)

    return published_measures_by_years_and_months


def get_published_dashboard_data():

    # GET DATA
    # get measures at their 1.0 publish date
    original_publications = (
        MeasureVersion.published_first_versions()
        .order_by(MeasureVersion.published_at.desc(), MeasureVersion.title)
        .all()
    )

    # get measures at their 2.0, 3.0 major update dates
    major_updates = (
        MeasureVersion.published_updates_first_versions()
        .order_by(MeasureVersion.published_at.desc(), MeasureVersion.title)
        .all()
    )

    # get first date to start point for data table
    first_publication = (
        MeasureVersion.query.filter(MeasureVersion.published_at.isnot(None))
        .order_by(MeasureVersion.published_at.asc())
        .first()
    )

    # BUILD CONTEXT
    # top level data
    data = {
        "number_of_publications": len(original_publications),
        "number_of_major_updates": len(major_updates),
        "first_publication": first_publication.published_at,
    }

    weeks = []
    cumulative_number_of_pages = []
    cumulative_number_of_major_updates = []

    # week by week rows
    for d in _from_month_to_month(first_publication.published_at, date.today()):
        c = calendar.Calendar(calendar.MONDAY).monthdatescalendar(d.year, d.month)
        for week in c:
            if _in_range(week, first_publication.published_at, d.month):

                publications = [page for page in original_publications if _page_in_week(page, week)]
                updates = [updated_page for updated_page in major_updates if _page_in_week(updated_page, week)]
                weeks.append({"week": week[0], "publications": publications, "major_updates": updates})

                if not cumulative_number_of_major_updates:
                    cumulative_number_of_major_updates.append(len(updates))
                else:
                    last_total = cumulative_number_of_major_updates[-1]
                    cumulative_number_of_major_updates.append(last_total + len(updates))

                if not cumulative_number_of_pages:
                    cumulative_number_of_pages.append(len(publications))
                else:
                    last_total = cumulative_number_of_pages[-1]
                    cumulative_number_of_pages.append(last_total + len(publications))

    weeks.reverse()
    data["weeks"] = weeks
    data["total_page_count_each_week"] = cumulative_number_of_pages
    data["total_major_updates_count_each_week"] = cumulative_number_of_major_updates

    return data


def get_ethnic_groups_dashboard_data():
    from application.dashboard.models import EthnicGroupByDimension

    links = EthnicGroupByDimension.query.all()

    # build a data structure with the links to count unique
    ethnicities = {}
    for link in sorted(links, key=lambda rec: rec.ethnicity_position):
        if link.ethnicity_value not in ethnicities:
            ethnicities[link.ethnicity_value] = {
                "value": link.ethnicity_value,
                "position": link.ethnicity_position,
                "url": url_for("dashboards.ethnic_group", value_slug=slugify(link.ethnicity_value)),
                "measure_ids": {link.measure_id},  # temporary list to allow calculating `count_measures` later
                "count_measures": 0,  # calculated afterwards using `measure_ids`
                "count_dimensions": 1,
                "classifications": {link.classification_title},
            }
        else:
            ethnicities[link.ethnicity_value]["measure_ids"].add(link.measure_id)
            ethnicities[link.ethnicity_value]["count_dimensions"] += 1
            ethnicities[link.ethnicity_value]["classifications"].add(link.classification_title)

    # Count the number of distinct measures for each ethnic group
    for ethnic_group in ethnicities.values():
        ethnic_group["count_measures"] = len(ethnic_group.pop("measure_ids"))

    return ethnicities.values()


def get_ethnic_group_by_slug_dashboard_data(ethnic_group_slug):
    ethnicity = classification_service.get_value_by_slug(ethnic_group_slug)

    ethnic_group_title = ""
    page_count = 0
    nested_measures_and_dimensions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    if ethnicity:
        ethnic_group_title = ethnicity.value
        from application.dashboard.models import EthnicGroupByDimension

        dimension_links = EthnicGroupByDimension.query.filter_by(ethnicity_value=ethnicity.value).all()

        for link in sorted(
            dimension_links,
            key=lambda rec: (rec.topic_title, rec.subtopic_position, rec.measure_position, rec.dimension_position),
        ):
            measure_dict = nested_measures_and_dimensions[link.topic_title][link.subtopic_title][
                link.measure_version_title
            ]

            measure_dict["title"] = link.measure_version_title
            measure_dict["url"] = url_for(
                "static_site.measure_version",
                topic_slug=link.topic_slug,
                subtopic_slug=link.subtopic_slug,
                measure_slug=link.measure_slug,
                version="latest",
            )
            measure_dict["dimensions"].append(
                {
                    "guid": link.dimension_guid,
                    "title": link.dimension_title,
                    "short_title": _calculate_short_title(link.measure_version_title, link.dimension_title),
                    "position": link.dimension_position,
                }
            )

    for (topic, measures_with_dimensions_by_subtopic) in nested_measures_and_dimensions.items():
        for subtopic, measures_with_dimensions in measures_with_dimensions_by_subtopic.items():
            page_count += len(measures_with_dimensions)

    return ethnic_group_title, page_count, nested_measures_and_dimensions


def get_ethnicity_classifications_dashboard_data():
    from application.dashboard.models import ClassificationByDimension

    all_classifications = classification_service.get_all_classifications()
    all_dimension_classifications = ClassificationByDimension.query.all()

    classifications = {
        classification.id: {
            "id": classification.id,
            "title": classification.long_title,
            "position": classification.position,
            "has_parents": len(classification.parent_values) > 0,
            "pages": set([]),
            "dimension_count": 0,
            "includes_parents_count": 0,
            "includes_all_count": 0,
            "includes_unknown_count": 0,
        }
        for classification in all_classifications
    }

    for link in all_dimension_classifications:
        classifications[link.classification_id]["pages"].add(link.measure_id)
        classifications[link.classification_id]["dimension_count"] += 1

        if link.includes_parents:
            classifications[link.classification_id]["includes_parents_count"] += 1
        if link.includes_all:
            classifications[link.classification_id]["includes_all_count"] += 1
        if link.includes_unknown:
            classifications[link.classification_id]["includes_unknown_count"] += 1

    ordered_and_filtered_classifications = sorted(
        filter(lambda x: x["dimension_count"] > 0, classifications.values()), key=lambda x: x["position"]
    )

    for classification in ordered_and_filtered_classifications:
        classification["measure_count"] = len(classification["pages"])

    return ordered_and_filtered_classifications


def get_ethnicity_classification_by_id_dashboard_data(classification_id):
    classification = classification_service.get_classification_by_id(classification_id)

    classification_title = ""
    page_count = 0
    nested_measures_and_dimensions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    if classification:
        classification_title = classification.long_title
        from application.dashboard.models import ClassificationByDimension

        dimension_links = ClassificationByDimension.query.filter_by(classification_id=classification_id).all()

        for link in sorted(
            dimension_links,
            key=lambda rec: (rec.topic_title, rec.subtopic_position, rec.measure_position, rec.dimension_position),
        ):
            measure_dict = nested_measures_and_dimensions[link.topic_title][link.subtopic_title][
                link.measure_version_title
            ]

            measure_dict["title"] = link.measure_version_title
            measure_dict["url"] = url_for(
                "static_site.measure_version",
                topic_slug=link.topic_slug,
                subtopic_slug=link.subtopic_slug,
                measure_slug=link.measure_slug,
                version="latest",
            )
            measure_dict["dimensions"].append(
                {
                    "guid": link.dimension_guid,
                    "title": link.dimension_title,
                    "short_title": _calculate_short_title(link.measure_version_title, link.dimension_title),
                    "position": link.dimension_position,
                }
            )

    for (topic, measures_with_dimensions_by_subtopic) in nested_measures_and_dimensions.items():
        for subtopic, measures_with_dimensions in measures_with_dimensions_by_subtopic.items():
            page_count += len(measures_with_dimensions)

    return classification_title, page_count, nested_measures_and_dimensions


def get_geographic_breakdown_dashboard_data():
    from application.dashboard.models import LatestPublishedMeasureVersionByGeography

    page_counts_by_geography = (
        LatestPublishedMeasureVersionByGeography.query.with_entities(
            LatestPublishedMeasureVersionByGeography.geography_name, func.count("*")
        )
        .group_by(
            LatestPublishedMeasureVersionByGeography.geography_name,
            LatestPublishedMeasureVersionByGeography.geography_position,
        )
        .order_by(LatestPublishedMeasureVersionByGeography.geography_position)
    )

    location_levels = []
    for geography_name, page_count in page_counts_by_geography:
        if page_count > 0:
            location_levels.append(
                {
                    "name": geography_name,
                    "url": url_for("dashboards.location", slug=slugify(geography_name)),
                    "pages": page_count,
                }
            )

    return location_levels


def get_geographic_breakdown_by_slug_dashboard_data(slug):
    # get the geography name from its slugified version
    geography = _deslugifiedLocation(slug)

    # get the measures that implement this as LatestPublishedMeasureVersionByGeography objects
    from application.dashboard.models import LatestPublishedMeasureVersionByGeography

    # Get measure version hierarchy for the given geographic area.
    measure_versions_with_geography = (
        LatestPublishedMeasureVersionByGeography.query.filter(
            LatestPublishedMeasureVersionByGeography.geography_name == geography.name
        )
    ).all()

    # Structure: {topic_title: {subtopic_title: [{title: mv_title, url: mv_url}, ...]}}
    measure_titles_and_urls_by_topic_and_subtopic = defaultdict(lambda: defaultdict(list))

    # Sort records by topic title, subtopic position, measure position. Relies on preserved dict insertion order.
    for record in sorted(
        measure_versions_with_geography, key=lambda rec: (rec.topic_title, rec.subtopic_position, rec.measure_position)
    ):
        measure_titles_and_urls_by_topic_and_subtopic[record.topic_title][record.subtopic_title].append(
            {
                "title": record.measure_version_title,
                "url": url_for(
                    "static_site.measure_version",
                    topic_slug=record.topic_slug,
                    subtopic_slug=record.subtopic_slug,
                    measure_slug=record.measure_slug,
                    version="latest",
                ),
            }
        )

    page_count = 0
    for topic, measures_by_subtopic in measure_titles_and_urls_by_topic_and_subtopic.items():
        for subtopic, measures in measures_by_subtopic.items():
            page_count += len(measures)

    return geography, page_count, measure_titles_and_urls_by_topic_and_subtopic


def get_planned_pages_dashboard_data():
    if not trello_service.is_initialised():
        raise TokenError("You need to set TRELLO_API_KEY and TRELLO_API_TOKEN environment variables.")

    # We exclude "done" from this list, as measures that have been published can be seen in the "Published measures"
    # dashboard. Also, the number of "Done" cards in the Trello board does not match the number of published measures
    # and updates, which could make the headline "Done" figure from this board confusing to users.
    stages_reported_in_dashboard = ("planned", "progress", "review")

    measure_cards = trello_service.get_measure_cards()
    measures = [measure for measure in measure_cards if measure["stage"] in stages_reported_in_dashboard]
    planned_count = len([measure for measure in measures if measure["stage"] == "planned"])
    progress_count = len([measure for measure in measures if measure["stage"] == "progress"])
    review_count = len([measure for measure in measures if measure["stage"] == "review"])

    return measures, planned_count, progress_count, review_count


def _calculate_short_title(page_title, dimension_title):
    # Case 1 - try stripping the dimension title
    low_title = dimension_title.lower()
    if low_title.find(page_title.lower()) == 0:
        return dimension_title[len(page_title) + 1 :]

    # Case 2 - try cutting using the last by
    by_pos = dimension_title.rfind("by")
    if by_pos >= 0:
        return dimension_title[by_pos:]

    # Case else - just return the original
    return dimension_title


def _deslugifiedLocation(slug):
    for location in LowestLevelOfGeography.query.all():
        if slugify(location.name) == slug:
            return location
    return None


def _from_month_to_month(start, end):
    current = start
    while current < end:
        yield current
        current += timedelta(days=current.max.day)
    yield current


def _in_range(week, begin, month, end=date.today()):
    if any([d for d in week if d.month > month]):
        return False
    return any([d for d in week if d >= begin]) and any([d for d in week if d <= end])


def _page_in_week(page, week):
    return page.published_at >= week[0] and page.published_at <= week[6]

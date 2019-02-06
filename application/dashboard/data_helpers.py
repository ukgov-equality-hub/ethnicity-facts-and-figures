import calendar
from collections import defaultdict
from datetime import date, timedelta

from flask import url_for
from slugify import slugify
from trello.exceptions import TokenError

from application.cms.classification_service import classification_service
from application.cms.models import MeasureVersion, LowestLevelOfGeography
from application.dashboard.trello_service import trello_service
from application.factory import page_service

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

    links = EthnicGroupByDimension.query.order_by(
        EthnicGroupByDimension.subtopic_guid,
        EthnicGroupByDimension.page_position,
        EthnicGroupByDimension.dimension_position,
        EthnicGroupByDimension.value_position,
    ).all()

    # build a data structure with the links to count unique
    ethnicities = {}
    for link in links:
        if link.value not in ethnicities:
            ethnicities[link.value] = {
                "value": link.value,
                "position": link.value_position,
                "url": url_for("dashboards.ethnic_group", value_slug=slugify(link.value)),
                "pages": {link.page_guid},
                "dimensions": 1,
                "classifications": {link.categorisation},
            }
        else:
            ethnicities[link.value]["dimensions"] += 1
            ethnicities[link.value]["pages"].add(link.page_guid)
            ethnicities[link.value]["classifications"].add(link.categorisation)
    for ethnic_group in ethnicities.values():
        ethnic_group["pages"] = len(ethnic_group["pages"])
        ethnic_group["classifications"] = len(ethnic_group["classifications"])

    # sort by standard ethnicity position
    return sorted(ethnicities.values(), key=lambda g: g["position"])


def get_ethnic_group_by_slug_dashboard_data(value_slug):
    ethnicity = classification_service.get_value_by_slug(value_slug)

    results = []
    page_count = 0
    value_title = ""
    if ethnicity:
        value_title = ethnicity.value
        from application.dashboard.models import EthnicGroupByDimension

        dimension_links = (
            EthnicGroupByDimension.query.filter_by(value=ethnicity.value)
            .order_by(
                EthnicGroupByDimension.subtopic_guid,
                EthnicGroupByDimension.page_position,
                EthnicGroupByDimension.dimension_position,
                EthnicGroupByDimension.value_position,
            )
            .all()
        )

        # Build a base tree of subtopics from the database
        subtopics = [
            {
                "guid": page.guid,
                "title": page.title,
                "slug": page.slug,
                "position": page.position,
                "topic_guid": page.parent_guid,
                "topic": page.parent.title,
                "topic_slug": page.parent.slug,
                "measures": [],
            }
            for page in page_service.get_pages_by_type("subtopic")
        ]
        subtopics = sorted(subtopics, key=lambda p: (p["topic_guid"], p["position"]))

        # Build a list of dimensions
        dimension_list = [
            {
                "dimension_guid": d.dimension_guid,
                "dimension_title": d.dimension_title,
                "dimension_position": d.dimension_position,
                "page_guid": d.page_guid,
                "page_title": d.page_title,
                "page_slug": d.page_slug,
                "page_position": d.page_position,
                "page_version": d.page_version,
                "subtopic_guid": d.subtopic_guid,
            }
            for d in dimension_links
        ]

        # Integrate with the topic tree
        for subtopic in subtopics:
            # Build a data structure of unique pages in the subtopic
            page_list = {
                d["page_guid"]: {
                    "guid": d["page_guid"],
                    "title": d["page_title"],
                    "slug": d["page_slug"],
                    "position": d["page_position"],
                    "url": url_for(
                        "static_site.measure_version",
                        topic_slug=subtopic["topic_slug"],
                        subtopic_slug=subtopic["slug"],
                        measure_slug=d["page_slug"],
                        version="latest",
                    ),
                }
                for d in dimension_list
                if d["subtopic_guid"] == subtopic["guid"]
            }

            # Integrate the list of dimensions
            for page in page_list.values():
                page["dimensions"] = [
                    {
                        "guid": d["dimension_guid"],
                        "title": d["dimension_title"],
                        "short_title": _calculate_short_title(page["title"], d["dimension_title"]),
                        "position": d["dimension_position"],
                    }
                    for d in dimension_list
                    if d["page_guid"] == page["guid"]
                ]

            subtopic["measures"] = sorted(page_list.values(), key=lambda p: p["position"])
            page_count += len(page_list)

        results = [s for s in subtopics if len(s["measures"]) > 0]

    return value_title, page_count, results


def get_ethnicity_classifications_dashboard_data():
    from application.dashboard.models import CategorisationByDimension

    dimension_links = CategorisationByDimension.query.all()
    classification_rows = classification_service.get_all_classifications()
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
        for classification in classification_rows
    }
    for link in dimension_links:
        classifications[link.categorisation_id]["pages"].add(link.page_guid)
        classifications[link.categorisation_id]["dimension_count"] += 1
        if link.includes_parents:
            classifications[link.categorisation_id]["includes_parents_count"] += 1
        if link.includes_all:
            classifications[link.categorisation_id]["includes_all_count"] += 1
        if link.includes_unknown:
            classifications[link.categorisation_id]["includes_unknown_count"] += 1

    classifications = list(classifications.values())
    classifications = [c for c in classifications if c["dimension_count"] > 0]
    classifications.sort(key=lambda x: x["position"])

    for classification in classifications:
        classification["measure_count"] = len(classification["pages"])

    return classifications


def get_ethnicity_classification_by_id_dashboard_data(classification_id):
    classification = classification_service.get_classification_by_id(classification_id)

    page_count = 0
    results = []
    classification_title = ""

    if classification:
        classification_title = classification.long_title
        from application.dashboard.models import CategorisationByDimension

        dimension_links = (
            CategorisationByDimension.query.filter_by(categorisation_id=classification_id)
            .order_by(
                CategorisationByDimension.subtopic_guid,
                CategorisationByDimension.page_position,
                CategorisationByDimension.dimension_position,
            )
            .all()
        )

        # Build a base tree of subtopics from the database
        subtopics = [
            {
                "guid": page.guid,
                "title": page.title,
                "slug": page.slug,
                "position": page.position,
                "topic_guid": page.parent_guid,
                "topic": page.parent.title,
                "topic_slug": page.parent.slug,
                "measures": [],
            }
            for page in page_service.get_pages_by_type("subtopic")
        ]
        subtopics = sorted(subtopics, key=lambda p: (p["topic_guid"], p["position"]))

        # Build a list of dimensions
        dimension_list = [
            {
                "dimension_guid": d.dimension_guid,
                "dimension_title": d.dimension_title,
                "dimension_position": d.dimension_position,
                "page_guid": d.page_guid,
                "page_title": d.page_title,
                "page_slug": d.page_slug,
                "page_position": d.page_position,
                "page_version": d.page_version,
                "subtopic_guid": d.subtopic_guid,
            }
            for d in dimension_links
        ]

        # Integrate with the topic tree
        for subtopic in subtopics:
            # Build a data structure of unique pages in the subtopic
            page_list = {
                d["page_guid"]: {
                    "guid": d["page_guid"],
                    "title": d["page_title"],
                    "slug": d["page_slug"],
                    "position": d["page_position"],
                    "url": url_for(
                        "static_site.measure_version",
                        topic_slug=subtopic["topic_slug"],
                        subtopic_slug=subtopic["slug"],
                        measure_slug=d["page_slug"],
                        version="latest",
                    ),
                }
                for d in dimension_list
                if d["subtopic_guid"] == subtopic["guid"]
            }

            # Integrate the list of dimensions
            for page in page_list.values():
                page["dimensions"] = [
                    {
                        "guid": d["dimension_guid"],
                        "title": d["dimension_title"],
                        "short_title": _calculate_short_title(page["title"], d["dimension_title"]),
                        "position": d["dimension_position"],
                    }
                    for d in dimension_list
                    if d["page_guid"] == page["guid"]
                ]

            subtopic["measures"] = sorted(page_list.values(), key=lambda p: p["position"])
            page_count += len(page_list)
        results = [s for s in subtopics if len(s["measures"]) > 0]

    return classification_title, page_count, results


def get_geographic_breakdown_dashboard_data():
    # build framework
    location_dict = {
        location.name: {"location": location, "pages": []} for location in LowestLevelOfGeography.query.all()
    }

    # integrate with page geography
    from application.dashboard.models import PageByLowestLevelOfGeography

    page_geogs = PageByLowestLevelOfGeography.query.all()
    for page_geog in page_geogs:
        location_dict[page_geog.geography_name]["pages"] += [page_geog.page_guid]

    # convert to list and sort
    location_list = list(location_dict.values())
    location_list.sort(key=lambda x: x["location"].position)

    location_levels = [
        {
            "name": item["location"].name,
            "url": url_for("dashboards.location", slug=slugify(item["location"].name)),
            "pages": len(item["pages"]),
        }
        for item in location_list
        if len(item["pages"]) > 0
    ]

    return location_levels


def get_geographic_breakdown_by_slug_dashboard_data(slug):
    # get the
    loc = _deslugifiedLocation(slug)

    # get the measures that implement this as PageByLowestLevelOfGeography objects
    from application.dashboard.models import PageByLowestLevelOfGeography

    measures = (
        PageByLowestLevelOfGeography.query.filter(PageByLowestLevelOfGeography.geography_name == loc.name)
        .order_by(PageByLowestLevelOfGeography.page_position)
        .all()
    )

    # Build a base tree of subtopics from the database
    subtopics = [
        {
            "guid": page.guid,
            "title": page.title,
            "slug": page.slug,
            "position": page.position,
            "topic_guid": page.parent_guid,
            "topic": page.parent.title,
            "topic_slug": page.parent.slug,
            "measures": [
                {
                    "title": measure.page_title,
                    "url": url_for(
                        "static_site.measure_version",
                        topic_slug=page.parent.slug,
                        subtopic_slug=page.slug,
                        measure_slug=measure.page_slug,
                        version="latest",
                    ),
                }
                for measure in measures
                if measure.subtopic_guid == page.guid
            ],
        }
        for page in page_service.get_pages_by_type("subtopic")
    ]

    # dispose of subtopics without content
    subtopics = [s for s in subtopics if len(s["measures"]) > 0]

    # sort
    subtopics.sort(key=lambda p: (p["topic_guid"], p["position"]))

    page_count = 0
    for subtopic in subtopics:
        page_count += len(subtopic["measures"])

    return loc, page_count, subtopics


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

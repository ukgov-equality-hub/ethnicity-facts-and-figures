import os

from application.data.dimensions import DimensionObjectBuilder
from application.cms.page_service import page_service


def build_index_json():
    # Grabbing everything and filtering is faster than going measure by measure and making calls backwards
    topics, subtopics, measures = get_all_pages()

    site_url = get_site_url()

    index = []
    for topic in topics:
        topic_subtopics = [subtopic for subtopic in subtopics if subtopic.parent_guid == topic.guid]
        for subtopic in topic_subtopics:
            subtopic_measures = page_service.get_latest_publishable_measures(subtopic)

            for measure in subtopic_measures:
                measure_object = {
                    "measure": measure.title,
                    "subtopic": subtopic.title,
                    "topic": topic.title,
                    "uri": "%s/%s/%s" % (topic.uri, subtopic.uri, measure.uri),
                    "url": "%s/%s/%s/%s/latest" % (site_url, topic.uri, subtopic.uri, measure.uri),
                }
                index = index + [measure_object]

    # filter out duplicate versions
    index = list({page["uri"]: page for page in index}.values())

    return index


def get_all_pages():
    topics = page_service.get_pages_by_type("topic")
    subtopics = page_service.get_pages_by_type("subtopic")
    measures = page_service.get_pages_by_type("measure")

    topics.sort(key=lambda page: page.uri)
    subtopics.sort(key=lambda page: page.uri)
    measures.sort(key=lambda page: page.uri)

    return topics, subtopics, measures


def build_measure_json(page):
    from application.static_site.filters import join_enum_display_names

    site_url = get_site_url()
    try:
        published_date = page.publication_date.isoformat()
    except Exception as e:
        published_date = ""

    try:
        subtopic = page_service.get_page(page.parent_guid)
        topic = page_service.get_page(subtopic.parent_guid)
        subtopic_title = subtopic.title
        topic_title = topic.title
        uri = "%s/%s/%s" % (topic.uri, subtopic.uri, page.uri)
        url = "%s/%s/%s/%s/%s" % (site_url, topic.uri, subtopic.uri, page.uri, page.version)
    except Exception as e:
        url = ""
        uri = ""
        subtopic_title = ""
        topic_title = ""

    return {
        "_measure": page.title,
        "_subtopic": subtopic_title,
        "_topic": topic_title,
        "_version": page.version,
        "uri": uri,
        "url": url,
        "data_sources": data_sources_for_api(page),
        "metadata": {
            "geographic_coverage": page.format_area_covered(),
            "frequency": page.frequency_of_release.description if page.frequency_of_release else "",
            "time_covered": page.time_covered,
            "data_type": join_enum_display_names(page.type_of_data, " and ") if page.type_of_data else "",
            "type_of_statistic": page.type_of_statistic_description.external
            if page.type_of_statistic_description
            else "",  # noqa
            "published_date": published_date,
            "qmi_url": page.qmi_url,
            "measure": page.title,
            "subtopic": subtopic_title,
            "topic": topic_title,
            "version": page.version,
        },
        "dimensions": [dimension_for_api(dimension) for dimension in page.dimensions],
        "downloads": [download_for_api(download, url) for download in page.uploads],
    }


def get_site_url():
    site_url = os.environ.get("RDU_SITE", "https://www.ethnicity-facts-figures.service.gov.uk")
    if site_url[-1] == "/":
        site_url = site_url[:-1]
    return site_url


def dimension_for_api(dimension):
    dimension_object = DimensionObjectBuilder.build(dimension)
    metadata = dimension_object["context"]
    title = metadata.get("dimension")

    if "table" in dimension_object:
        data = dimension_object["table"]["data"]
    elif "chart" in dimension_object:
        data = dimension_object["chart"]["data"]
    else:
        data = []

    return {"_dimension": title, "metadata": metadata, "data": data}


def download_for_api(download, url):
    return {"title": download.title, "file_name": download.file_name, "full_path": "%s/%s" % (url, download.file_name)}


def data_sources_for_api(page):
    sources = [
        {
            "publisher": page.department_source.name if page.department_source else "",
            "title": page.source_text,
            "url": page.source_url,
        }
    ]

    if page.secondary_source_1_publisher is not None:
        secondary_source = {
            "publisher": page.secondary_source_1_publisher.name,
            "title": page.secondary_source_1_title,
            "url": page.secondary_source_1_url,
        }
        sources = sources + [secondary_source]

    return sources

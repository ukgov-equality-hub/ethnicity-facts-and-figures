from application.cms.page_service import page_service
import os


def build_index_json():
    # Grabbing everything and filtering is faster than going measure by measure and making calls backwards
    topics, subtopics, measures = get_all_pages()

    site_url = os.environ.get('RDU_SITE', '')

    index = []
    for topic in topics:
        topic_subtopics = [subtopic for subtopic in subtopics if subtopic.parent_guid == topic.guid]
        for subtopic in topic_subtopics:
            subtopic_measures = [measure for measure in measures
                                 if measure.parent_guid == subtopic.guid and measure.status == 'APPROVED']
            for measure in subtopic_measures:
                measure_object = {
                    'measure': measure.title,
                    'subtopic': subtopic.title,
                    'topic': topic.title,
                    'uri': '%s/%s/%s' % (topic.uri, subtopic.uri, measure.uri),
                    'url': '%s/%s/%s/%s/latest' % (site_url, topic.uri, subtopic.uri, measure.uri)
                }
                index = index + [measure_object]

    # filter out duplicate versions
    index = list({page['uri']: page for page in index}.values())

    return index


def get_all_pages():
    topics = page_service.get_pages_by_type('topic')
    subtopics = page_service.get_pages_by_type('subtopic')
    measures = page_service.get_pages_by_type('measure')

    topics.sort(key=lambda page: page.uri)
    subtopics.sort(key=lambda page: page.uri)
    measures.sort(key=lambda page: page.uri)

    return topics, subtopics, measures

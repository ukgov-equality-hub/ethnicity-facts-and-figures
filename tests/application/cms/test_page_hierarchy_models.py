from tests.models import TopicFactory, SubtopicFactory, MeasureFactory


def test_references_between_subtopic_and_topic():
    topic = TopicFactory()
    subtopic = SubtopicFactory(topic=topic)

    assert topic.subtopics == [subtopic]
    assert subtopic.topic == topic


def test_reference_from_subtopic_to_measures():
    # Given a subtopic with no measures
    subtopic = SubtopicFactory()
    assert subtopic.measures == []

    # When a subtopic is added to a measure
    measure1 = MeasureFactory(subtopics=[])
    measure1.subtopics.append(subtopic)

    # Then the subtopic has that measure in its measures list
    assert subtopic.measures == [measure1]

    # When another measure has the same subtopic
    measure2 = MeasureFactory(subtopics=[])
    measure2.subtopics.append(subtopic)

    # Then both measures are in the measures list
    assert subtopic.measures == [measure1, measure2]


def test_reference_from_measure_to_subtopics():
    # Given a measure with no subtopic
    measure1 = MeasureFactory(subtopics=[])
    assert measure1.subtopics == []

    # When a measure is added to a subtopic
    subtopic = SubtopicFactory()
    subtopic.measures.append(measure1)

    # Then the measure has that subtopic in its subtopics list
    assert measure1.subtopics == [subtopic]

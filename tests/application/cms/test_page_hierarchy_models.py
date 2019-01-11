from application.cms.models import Subtopic, Measure


def test_references_between_subtopic_and_topic(stub_topic, stub_subtopic):
    assert stub_topic.subtopics == [stub_subtopic]
    assert stub_subtopic.topic == stub_topic


def test_reference_from_subtopic_to_measures():
    # Given a subtopic with no measures
    subtopic = Subtopic()
    assert subtopic.measures == []

    # When a subtopic is added to a measure
    measure_1 = Measure()
    measure_1.subtopics.append(subtopic)

    # Then the subtopic has that measure in its measures list
    assert subtopic.measures == [measure_1]

    # When another measure has the same subtopic
    measure_2 = Measure()
    measure_2.subtopics.append(subtopic)

    # Then both measures are in the measures list
    assert subtopic.measures == [measure_1, measure_2]


def test_reference_from_measure_to_subtopics():
    # Given a measure with no subtopic
    measure = Measure()
    assert measure.subtopics == []

    # When a measure is added to a subtopic
    subtopic = Subtopic()
    subtopic.measures.append(measure)

    # Then the measure has that subtopic in its subtopics list
    assert measure.subtopics == [subtopic]

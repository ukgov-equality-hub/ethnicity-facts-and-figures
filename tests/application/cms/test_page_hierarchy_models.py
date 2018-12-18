def test_references_between_subtopic_and_topic(stub_topic, stub_subtopic):
    assert stub_topic.subtopics == [stub_subtopic]
    assert stub_subtopic.topic == stub_topic


def test_reference_from_subtopic_to_measures(stub_subtopic, stub_measure_1, stub_measure_2):
    # Given a subtopic with no measures
    assert stub_subtopic.measures == []
    # When a subtopic is added to a measure
    stub_measure_1.subtopics.append(stub_subtopic)
    # Then the subtopic has that measure in its measures list
    assert stub_subtopic.measures == [stub_measure_1]
    # When another measure has the same subtopic
    stub_measure_2.subtopics.append(stub_subtopic)
    # Then both measures are in the measures list
    assert stub_subtopic.measures == [stub_measure_1, stub_measure_2]


def test_reference_from_measure_to_subtopics(stub_subtopic, stub_measure_1, stub_measure_2):
    # Given a measure with no subtopic
    assert stub_measure_1.subtopics == []
    # When a measure is added to a subtopic
    stub_subtopic.measures.append(stub_measure_1)
    # Then the measure has that subtopic in its subtopics list
    assert stub_measure_1.subtopics == [stub_subtopic]

import pytest

from application.cms.models import Measure, Subtopic, Topic


@pytest.fixture(scope="function")
def stub_topic(db_session):
    topic = Topic(
        slug="test-topic",
        title="Test topic page",
        description="A topic for testing",
        additional_description="This is a topic to use in tests",
    )

    db_session.session.add(topic)
    db_session.session.commit()
    return topic


@pytest.fixture(scope="function")
def stub_subtopic(db_session, stub_topic):
    subtopic = Subtopic(slug="test-subtopic", title="Test subtopic page", position=1, topic_id=stub_topic.id)

    db_session.session.add(subtopic)
    db_session.session.commit()
    return subtopic


@pytest.fixture(scope="function")
def stub_measure_1(db_session, stub_subtopic):
    measure = Measure(slug="test-measure-1", position=1, reference="RDU TEST 1")

    db_session.session.add(measure)
    db_session.session.commit()
    return measure


@pytest.fixture(scope="function")
def stub_measure_2(db_session, stub_subtopic):
    measure = Measure(slug="test-measure-2", position=2, reference="RDU TEST 2")

    db_session.session.add(measure)
    db_session.session.commit()
    return measure

from application.cms.models import Measure
from application.auth.models import TypeOfUser


from tests.functional.pages import HomePage, TopicPage, MeasureEditPage, MeasureCreatePage, RandomMeasure
from tests.functional.utils import driver_login
from tests.models import MeasureVersionFactory, UserFactory
from tests.utils import get_page_with_title

"""

THIS TEST CREATES THEN DELETES A MEASURE AT THE DRAFT 1.0 STAGE

"""


def test_delete_a_draft_1_0_measure(driver, live_server):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
    measure_version = MeasureVersionFactory(status="APPROVED", published=True)

    assert Measure.query.count() == 1

    # GIVEN we create a version 1.0 measure
    driver_login(driver, live_server, rdu_user)
    navigate_to_topic_page(driver, live_server, measure_version.measure.subtopic.topic)
    measure = create_measure_with_minimal_content(
        driver, live_server, measure_version.measure.subtopic, measure_version.measure.subtopic.topic
    )

    assert Measure.query.count() == 2

    # WHEN we go to the topic page
    topic_page = TopicPage(driver, live_server, measure_version.measure.subtopic.topic)
    topic_page.get()

    # No longer required; accordion remembers the expanded state from earlier in the test.
    # topic_page.expand_accordion_for_subtopic(measure_version.measure.subtopic)

    # THEN measure is listed
    assert topic_page.measure_is_listed(measure) is True

    driver.find_element_by_link_text(measure.title).click()

    # WHEN we walk through the delete process
    driver.find_element_by_link_text("Delete").click()

    driver.find_element_by_xpath('//button[text()="Yes, delete"]').click()

    topic_page.get()
    # This test has been passing when the final .get() returned a 500 error page.
    # TODO: Check the page didn't error and is the actual page we expect to not find the thing in
    # TODO: Maybe assert 200 responses after all get()s in functional tests?
    assert topic_page.measure_is_listed(measure) is False

    assert Measure.query.count() == 1


def create_measure_with_minimal_content(driver, live_server, stub_subtopic_page, stub_topic_page):
    """
    CREATE v1 1: Click through to subtopic topic page
    """
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    assert topic_page.is_current()
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)
    """
    CREATE v1 2: Add measure page
    """
    topic_page.click_add_measure(stub_subtopic_page)
    measure_create_page = MeasureCreatePage(driver, live_server, stub_topic_page, stub_subtopic_page)
    assert measure_create_page.is_current()
    """
    CREATE v1 3: Fill measure create page
    """
    page = RandomMeasure()
    measure_create_page.set_title(page.title)
    measure_create_page.click_save()

    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.click_breadcrumb_for_page(stub_topic_page)

    """
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so
    we have to retrieve the page again
    """
    page = get_page_with_title(page.title)
    return page


def navigate_to_topic_page(driver, live_server, topic_page):
    """
    ENTRY 1: Home page
    """
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()
    """
    ENTRY 1: Go to topic page
    """
    home_page.click_topic_link(topic_page)


def navigate_to_preview_page(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_preview_measure(measure)


def navigate_to_edit_page(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_get_measure(measure)

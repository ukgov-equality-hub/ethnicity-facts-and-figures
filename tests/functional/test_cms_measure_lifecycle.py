import pytest

from application.cms.page_service import PageService
from flask import current_app

from tests.functional.pages import (
    LogInPage,
    HomePage,
    TopicPage,
    MeasureEditPage,
    MeasureCreatePage,
    RandomMeasure
)

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')

'''

THIS TEST WALKS THROUGH THE MEASURE LIFECYCLE

'''

EXPECTED_STATUSES = {'draft': 'Status:  Draft',
                     'internal_review': 'Status:  Internal review',
                     'department_review': 'Status:  Department review',
                     'published': 'Status:  Published',
                     'rejected': 'Status:  Rejected'}


def test_create_a_measure_as_editor(driver,
                                    test_app_editor,
                                    test_app_admin,
                                    live_server,
                                    stub_topic_page,
                                    stub_subtopic_page):
    # GIVEN a setup with Topic and Subtopic
    login(driver, live_server, test_app_editor)
    navigate_to_topic_page(driver, live_server, stub_topic_page)

    # WHEN an editor creates and saves a new measure page
    measure_edit_page, page = create_measure_starting_at_topic_page(driver,
                                                                    live_server,
                                                                    stub_subtopic_page,
                                                                    stub_topic_page)

    # THEN the status should be draft
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['draft']

    measure_edit_page.click_save_and_send_to_review()

    # THEN the status should be internal review
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['internal_review']

    # WHEN we send page to department review
    measure_edit_page.click_department_review()

    # THEN the status should be department review
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['department_review']

    # AND the approve button should not be on page
    assert measure_edit_page.approved_is_visible() is False

    # GIVEN the department link
    review_link = measure_edit_page.get_review_link()

    # WHEN we log out and go to the review link
    measure_edit_page.log_out()
    driver.get(review_link)

    # THEN the preview page ought to have content
    assert page.title in driver.page_source

    # GIVEN the admin user
    login(driver, live_server, test_app_admin)

    # WHEN we go to the edit page
    navigate_to_topic_page(driver, live_server, stub_topic_page)
    navigate_to_view_form(driver, live_server, stub_topic_page, stub_subtopic_page, page)

    # THEN the approve button is visible
    assert measure_edit_page.approved_is_visible() is True

    # WHEN the admin user clicks approve
    measure_edit_page.click_approved()

    # THEN the status should be published
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['published']

    measure_edit_page.log_out()


def test_can_reject_a_measure_in_review_as_editor(driver,
                                                  test_app_editor,
                                                  test_app_admin,
                                                  live_server,
                                                  stub_topic_page,
                                                  stub_subtopic_page):
    # GIVEN a setup with Topic and Subtopic
    login(driver, live_server, test_app_editor)
    navigate_to_topic_page(driver, live_server, stub_topic_page)

    # WHEN an editor creates and saves a new measure page
    measure_edit_page, page = create_measure_starting_at_topic_page(driver,
                                                                    live_server,
                                                                    stub_subtopic_page,
                                                                    stub_topic_page)

    # THEN the status should be draft
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['draft']

    # WHEN we save and send it to internal review
    measure_edit_page.click_save_and_send_to_review()

    # THEN the status should be internal review
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['internal_review']

    # WHEN we reject the page
    measure_edit_page.click_reject()

    # THEN the status should be rejected
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['rejected']

    # WHEN we send it back to a draft
    measure_edit_page.click_send_back_to_draft()

    # THEN the status should be draft
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['draft']

    # WHEN we save and send it for department review
    measure_edit_page.click_save_and_send_to_review()
    measure_edit_page.click_department_review()

    # THEN the status should be department review
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['department_review']

    # WHEN we reject the measure again
    review_link = measure_edit_page.click_reject()

    # THEN the status should be rejected
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES['rejected']

    measure_edit_page.log_out()


def assert_page_correct(driver, live_server, stub_topic_page, stub_subtopic_page, page, status):
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)

    assert_page_status(driver, topic_page, page, status)

    topic_page.click_preview_measure(page)
    assert_page_details(driver, page)

    driver.back()


def assert_page_status(driver, topic_page, page, status):
    pass


def assert_page_details(driver, page):
    pass


def create_measure_starting_at_topic_page(driver, live_server, stub_subtopic_page, stub_topic_page):
    '''
    CREATE v1 1: Click through to subtopic topic page
    '''
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    assert topic_page.is_current()
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)
    '''
    CREATE v1 2: Add measure page
    '''
    topic_page.click_add_measure(stub_subtopic_page)
    measure_create_page = MeasureCreatePage(driver, live_server, stub_topic_page, stub_subtopic_page)
    assert measure_create_page.is_current()
    '''
    CREATE v1 3: Fill measure create page
    '''
    page = RandomMeasure()
    measure_create_page.set_title(page.title)
    measure_create_page.click_save()
    '''
    CREATE v1 4: Add some content
    '''
    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.fill_measure_page(page)
    measure_edit_page.click_save()
    '''
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so
    we may have to retrieve the page again
    '''
    page_service = PageService()
    page = page_service.get_page_with_title(page.title)
    return measure_edit_page, page


def navigate_to_topic_page(driver, live_server, topic_page):
    '''
    ENTRY 1: Home page
    '''
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()
    '''
    ENTRY 1: Go to topic page
    '''
    home_page.click_topic_link(topic_page)


def navigate_to_preview_page(driver, live_server, topic, subtopic, measure):
    '''
    ENTRY 1: Home page
    '''
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_preview_measure(measure)


def navigate_to_edit_page(driver, live_server, topic, subtopic, measure):
    '''
    ENTRY 1: Home page
    '''
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_edit_button(measure)


def navigate_to_view_form(driver, live_server, topic, subtopic, measure):
    '''
    ENTRY 1: Home page
    '''
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_view_form_button(measure)


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

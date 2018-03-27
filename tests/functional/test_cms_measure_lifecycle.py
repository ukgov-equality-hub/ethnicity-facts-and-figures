import pytest

from application.cms.page_service import PageService
from tests.functional.pages import (
    LogInPage,
    HomePage,
    CmsIndexPage,
    TopicPage,
    SubtopicPage,
    MeasureVersionsPage,
    MeasureEditPage,
    MeasureCreatePage,
    RandomMeasure
)

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')

'''

THIS SUITE OF TESTS WALKS THROUGH THE MEASURE LIFECYCLE

'''

def test_create_a_measure_as_editor(driver,
                                    test_app_editor,
                                    test_app_admin,
                                    live_server,
                                    stub_topic_page,
                                    stub_subtopic_page):
    expected_statuses = {'draft':'Status:  Draft',
                         'internal_review': 'Status:  Internal review',
                         'department_review': 'Status:  Department review',
                         'published': 'Status:  Published'}

    # GIVEN a setup with Topic and Subtopic
    login(driver, live_server, test_app_editor)
    navigate_to_topic_page(driver, live_server, stub_topic_page)

    # WHEN an editor creates and saves a new measure page
    measure = create_measure_starting_at_topic_page(driver, live_server, stub_subtopic_page, stub_topic_page)

    # THEN the status should be draft
    navigate_to_edit_page(driver, live_server, stub_topic_page, stub_subtopic_page, measure)
    measure_edit_page = MeasureEditPage(driver)
    assert measure_edit_page.get_status() == expected_statuses['draft']

    # WHEN we return to the edit page and save to review
    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.click_save_and_send_to_review()

    # THEN the status should be internal review
    measure_edit_page = MeasureEditPage(driver)
    assert measure_edit_page.get_status() == expected_statuses['internal_review']

    # WHEN we return to the edit page and promote to department review
    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.click_department_review()

    # THEN the status should be department review
    measure_edit_page = MeasureEditPage(driver)
    assert measure_edit_page.get_status() == expected_statuses['department_review']

    # AND the approve link should not appear
    assert measure_edit_page.approved_is_visible() == False

    # GIVEN the department link
    review_link = measure_edit_page.get_review_link()

    # WHEN we log out and go to the review link
    measure_edit_page.log_out()
    driver.get(review_link)

    # THEN the preview page ought to have content
    assert measure.title in driver.page_source;

    # GIVEN the admin user
    login(driver, live_server, test_app_admin)

    # WHEN we go to the edit page
    navigate_to_topic_page(driver, live_server, stub_topic_page)
    navigate_to_edit_page(driver, live_server, stub_topic_page, stub_subtopic_page, measure)

    # THEN the approve button is visible
    assert measure_edit_page.approved_is_visible() == True

    # WHEN the admin user clicks approve
    measure_edit_page.click_approved()

    # THEN the status should be published
    measure_edit_page = MeasureEditPage(driver)
    assert measure_edit_page.get_status() == expected_statuses['published']


def test_delete_a_draft_1_0_measure(driver,
                                    test_app_editor,
                                    live_server,
                                    stub_topic_page,
                                    stub_subtopic_page):
    # GIVEN we create a version 1.0 measure
    login(driver, live_server, test_app_editor)
    navigate_to_topic_page(driver, live_server, stub_topic_page)
    measure = create_measure_with_minimal_content(driver, live_server, stub_subtopic_page, stub_topic_page)

    # WHEN we go to the topic page
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    topic_page.get()
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)

    # THEN measure is listed
    assert topic_page.measure_is_listed(measure)



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
    measure_edit_page.click_breadcrumb_for_page(stub_topic_page)
    '''
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so 
    we have to retrieve the page again
    '''
    page_service = PageService()
    page = page_service.get_page_with_title(page.title)
    return page


def create_measure_with_minimal_content(driver, live_server, stub_subtopic_page, stub_topic_page):
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
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so 
    we have to retrieve the page again
    '''
    page_service = PageService()
    page = page_service.get_page_with_title(page.title)
    return page


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
    topic_page.click_get_measure(measure)


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

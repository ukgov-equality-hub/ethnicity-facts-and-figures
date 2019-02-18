from random import shuffle

from tests.functional.pages import (
    HomePage,
    LogInPage,
    MeasureCreatePage,
    MeasureEditPage,
    RandomMeasure,
    TopicPage,
    RandomDataSource,
)
from tests.utils import get_page_with_title

EXPECTED_STATUSES = {
    "draft": "Status:  Draft",
    "internal_review": "Status:  Internal review",
    "department_review": "Status:  Department review",
    "published": "Status:  Published",
    "rejected": "Status:  Rejected",
}


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
    data_source = RandomDataSource()
    measure_create_page.set_title(page.title)
    measure_create_page.click_save()
    """
    CREATE v1 4: Add some content
    """
    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.fill_measure_page(page, data_source)
    measure_edit_page.click_save()
    """
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so
    we may have to retrieve the page again
    """
    page = get_page_with_title(page.title)
    return measure_edit_page, page


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
    topic_page.click_measure_title(measure)


def navigate_to_edit_page(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """

    driver.find_element_by_link_text(topic.title).click()

    # Open the accordion section for the sub-topic
    driver.find_element_by_xpath(f"//h2[normalize-space(text())='{subtopic.title}']").click()

    driver.find_element_by_link_text(measure.title).click()

    driver.find_element_by_link_text("Edit").click()


def navigate_to_view_form(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
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


def spaceless(string_list):
    def despace(s):
        return "".join(s.split())

    return [despace(s) for s in string_list]


def go_to_page(page):
    page.get()
    assert page.is_current()
    return page


def assert_page_contains(page, text):
    return page.source_contains(text)


def create_measure(driver, live_server, page, topic, subtopic):
    create_measure_page = MeasureCreatePage(driver, live_server, topic, subtopic)
    create_measure_page.set_title(page.title)
    create_measure_page.click_save()


def new_create_measure(driver, live_server, measure_version):
    create_measure_page = MeasureCreatePage(
        driver, live_server, measure_version.measure.subtopic.topic, measure_version.measure.subtopic
    )
    create_measure_page.set_title(measure_version.title)
    create_measure_page.click_save()


def shuffle_table(table):
    table_body = table[1:]
    shuffle(table_body)
    return [table[0]] + table_body


def driver_login(driver, live_server, user):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(user.email, user.password)

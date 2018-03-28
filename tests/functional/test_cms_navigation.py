import pytest
from tests.functional.pages import (
    LogInPage,
    HomePage,
    CmsIndexPage,
    TopicPage,
    SubtopicPage,
    MeasureVersionsPage,
    MeasureEditPage
)

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_can_navigate_to_edit_measure_page(driver,
                                           test_app_editor,
                                           live_server,
                                           stub_topic_page,
                                           stub_subtopic_page,
                                           stub_measure_page):

    login(driver, live_server, test_app_editor)

    '''
    Home page
    '''
    home_page = HomePage(driver, live_server)
    assert home_page.is_current()

    '''
        Go to topic page
    '''
    home_page.click_topic_link(stub_topic_page)

    '''
       Click through to subtopic topic page
    '''
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    assert topic_page.is_current()
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)

    '''
        Go to add measure page
    '''
    topic_page.click_get_measure(stub_measure_page)

    measure_page = MeasureEditPage(driver)
    '''
    Check measure page navigation
    '''
    assert measure_page.is_current()

    measure_page.click_breadcrumb_for_home()
    assert home_page.is_current()

    measure_page.get()

    measure_page.click_breadcrumb_for_page(stub_topic_page)
    assert topic_page.is_current()


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

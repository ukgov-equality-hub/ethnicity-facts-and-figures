import pytest
from tests.functional.pages import LogInPage, IndexPage, CmsIndexPage, TopicPage, SubtopicPage, MeasureEditPage

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_can_navigate_to_edit_measure_page(driver,  test_app_editor, live_server,
                                           stub_topic_page, stub_subtopic_page, stub_measure_page):

    login(driver, live_server, test_app_editor)

    '''
    Home page
    '''
    index_page = IndexPage(driver, live_server)
    assert index_page.is_current()

    '''
    Click through to cms page
    '''
    index_page.click_cms_link()
    cms_index_page = CmsIndexPage(driver, live_server)
    assert cms_index_page.is_current()

    '''
    Click through to topic page
    '''
    cms_index_page.click_topic_link(stub_topic_page)
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    assert topic_page.is_current()

    '''
    Click through to subtopic page
    '''
    topic_page.click_subtopic_link(stub_subtopic_page)
    subtopic_page = SubtopicPage(driver, live_server, stub_topic_page, stub_subtopic_page)
    assert subtopic_page.is_current()

    '''
    Click through to measure page
    '''
    subtopic_page.click_measure_link(stub_measure_page)
    measure_page = MeasureEditPage(driver, live_server, stub_topic_page, stub_subtopic_page, stub_measure_page.guid)
    assert measure_page.is_current()

    '''
    Check measure page navigation
    '''
    measure_page.get()
    measure_page.click_breadcrumb_for_home()
    assert cms_index_page.is_current()

    measure_page.get()
    measure_page.click_breadcrumb_for_page(stub_topic_page)
    assert topic_page.is_current()

    measure_page.get()
    measure_page.click_breadcrumb_for_page(stub_subtopic_page)
    assert subtopic_page.is_current()

    '''
    Check subtopic page navigation
    '''
    subtopic_page.get()
    subtopic_page.click_breadcrumb_for_home()
    assert cms_index_page.is_current()

    subtopic_page.get()
    subtopic_page.click_breadcrumb_for_page(stub_topic_page)
    assert topic_page.is_current()

    '''
    Check topic page navigation
    '''
    topic_page.get()
    topic_page.click_breadcrumb_for_home()
    assert cms_index_page.is_current()


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)


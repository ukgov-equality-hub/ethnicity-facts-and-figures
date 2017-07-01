import pytest
from tests.functional.pages import LogInPage, IndexPage, CmsIndexPage, TopicPage, SubtopicPage, MeasureEditPage, \
    MeasureCreatePage

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')

def test_can_create_a_measure_page(driver,  test_app_editor, live_server,
                                           stub_topic_page, stub_subtopic_page, stub_measure_page):

    login(driver, live_server, test_app_editor)

    '''
    Go to a subtopic page
    '''
    subtopic_page = SubtopicPage(driver, live_server, stub_topic_page, stub_subtopic_page)
    subtopic_page.get()
    assert subtopic_page.is_current()

    '''
    Click create measure
    '''
    subtopic_page.click_new_measure()

    create_measure_page = MeasureCreatePage(driver, live_server, stub_topic_page, stub_subtopic_page)
    create_measure_page.set_guid('blah')
    create_measure_page.set_title('blah di blah di blah di blah etc')

    create_measure_page.click_save()
    import time
    time.sleep(10)


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

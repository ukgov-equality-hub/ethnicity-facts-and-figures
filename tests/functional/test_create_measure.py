import pytest
from tests.functional.pages import LogInPage, IndexPage, CmsIndexPage

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_everything(driver,  test_app_editor, live_server):

    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

    index_page = IndexPage(driver, live_server)
    assert index_page.is_current()

    index_page.click_cms_link()

    cms_index_page = CmsIndexPage(driver, live_server)
    assert cms_index_page.is_current()

from tests.functional.pages import HomePage


def test_can_search_from_homepage_with_javascript(driver, live_server):
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()

    home_page.search_site("health")

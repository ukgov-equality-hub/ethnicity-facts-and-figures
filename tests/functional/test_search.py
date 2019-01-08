from tests.functional.pages import HomePage


def test_site_search_form_action_updated_by_javascript(driver, live_server):
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()

    expected_url = f"http://localhost:{live_server.port}/search"
    assert driver.find_element_by_id("search-form").get_attribute("action") == expected_url


def test_can_search_from_homepage_with_javascript(driver, live_server):
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()

    home_page.search_site("health")

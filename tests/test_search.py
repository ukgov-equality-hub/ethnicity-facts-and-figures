from flask import url_for
from bs4 import BeautifulSoup

from application.config import Config


def test_homepage_search_links_to_google_custom_url_before_javascript(test_app_client,
                                                                      mock_admin_user,
                                                                      stub_topic_page):
        resp = test_app_client.get(url_for('static_site.search'))

        assert resp.status_code == 200
        page = BeautifulSoup(resp.get_data(as_text=True), 'html.parser')

        search_forms = page.header.select('form#search-form')
        assert len(search_forms) == 1

        assert search_forms[0]['action'] == 'https://cse.google.com/cse/publicurl'
        assert search_forms[0].select('[name=cx]')[0]['value'] == Config.GOOGLE_CUSTOM_SEARCH_URI

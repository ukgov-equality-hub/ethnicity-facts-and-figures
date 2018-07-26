from flask import url_for
from bs4 import BeautifulSoup

from application.config import Config


def test_homepage_includes_mailing_list_sign_up(test_app_client):

    response = test_app_client.get(url_for('static_site.index'))

    assert response.status_code == 200
    page = BeautifulSoup(response.get_data(as_text=True), 'html.parser')

    assert page.select_one("form[action=" + config.NEWSLETTER_SUBSCRIBE_URL "]"), "Mailing list subscription form should be present"
    assert page.select_one('label', text='Email address'), "E-mail address label should be present"
    assert page.select_one('input[name=EMAIL]'), "E-mail address field should be present"
    assert page.select_one('button', text='Subscribe'), "Subscribe button should be present"

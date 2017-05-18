import pytest

from flask import url_for
from bs4 import BeautifulSoup


pytestmark = pytest.mark.usefixtures('mock_user', 'mock_page_service_get_pages')


def test_logged_out_user_redirects_to_login(client):

    resp = client.get(url_for('cms.index'))

    assert resp.status_code == 302
    assert resp.location == url_for('security.login', next='/', _external=True)


def test_successfully_logged_in_user_goes_to_main_page(client):

    resp = client.post(
            url_for('security.login'),
            data={'email': 'test@example.com', 'password': 'password123'},
            follow_redirects=True
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.string.strip() == 'Government data on ethnicity'


def test_unsuccessful_login_returns_to_login_page(client):

    resp = client.post(
            url_for('security.login'),
            data={'email': 'notauser@example.com', 'password': 'password123'},
            follow_redirects=True
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.string.strip() == 'Login'

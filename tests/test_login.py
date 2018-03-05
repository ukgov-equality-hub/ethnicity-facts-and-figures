import pytest

from flask import url_for
from bs4 import BeautifulSoup


def test_logged_out_user_redirects_to_login(test_app_client):
    resp = test_app_client.get(url_for('static_site.index'))

    assert resp.status_code == 302
    assert resp.location == url_for('security.login', next='/', _external=True)


def test_successfully_logged_in_user_goes_to_main_page(test_app_client, mock_user):

    resp = test_app_client.post(
            url_for('security.login'),
            data={'email': mock_user.email, 'password': mock_user.password},
            follow_redirects=True
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert 'Ethnicity facts and figures' == page.h1.string.strip()


def test_unsuccessful_login_returns_to_login_page(test_app_client):

    resp = test_app_client.post(
            url_for('security.login'),
            data={'email': 'notauser@example.com', 'password': 'password123'},
            follow_redirects=True
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.string.strip() == 'Login'

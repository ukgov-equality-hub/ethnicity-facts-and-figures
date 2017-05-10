import pytest

from flask import url_for
from bs4 import BeautifulSoup

pytestmark = pytest.mark.usefixtures('mock_page_service_get_pages', 'mock_get_page')


def test_create_page(client, mock_user, mock_create_page, mock_get_page, stub_page):

    with client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = client.post(url_for('cms.create_topic_page'),
                       data={'title': stub_page.title, 'description': stub_page.description},
                       follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Created page %s' % stub_page.title
    assert page.find('textarea', id='description').string == stub_page.description

    mock_create_page.assert_called_once_with(data={'title': stub_page.title, 'description': stub_page.description},
                                             page_type='topic')
    mock_get_page.assert_called_once_with(stub_page.meta.uri)


def test_reject_page(client, mock_user, stub_page, mock_reject_page):

    with client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = client.get(url_for('cms.reject_page', slug=stub_page.meta.uri), follow_redirects=True)
    assert resp.status_code == 200
    mock_reject_page.assert_called_once_with(stub_page.meta.uri)

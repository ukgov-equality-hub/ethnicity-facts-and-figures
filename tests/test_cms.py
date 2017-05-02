import pytest

from flask import url_for
from bs4 import BeautifulSoup

pytestmark = pytest.mark.usefixtures('mock_page_service_get_pages')


def test_create_page(client, mock_user, mock_create_page):

    with client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = client.post(url_for('cms.create_page'),
                       data={'title': 'Test topic', 'description': 'This is the description'},
                       follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Created page Test topic'
    assert page.find('textarea', id='description').string == 'This is the description'

    mock_create_page.assert_called_once_with(data={'title': 'Test topic', 'description': 'This is the description'})

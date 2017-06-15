import pytest

from flask import url_for
from bs4 import BeautifulSoup

from application.cms.forms import MeasurePageForm

pytestmark = pytest.mark.usefixtures('mock_page_service_get_pages')


def test_create_measure_page(test_app_client,
                             mock_user,
                             mock_create_page,
                             mock_get_page,
                             stub_topic_page,
                             stub_subtopic_page,
                             stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    form = MeasurePageForm(obj=stub_measure_page)

    resp = test_app_client.post(url_for('cms.create_measure_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid), data=form.data, follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Created page %s' % stub_measure_page.title

    mock_create_page.assert_called_with(data=form.data,
                                        page_type='measure',
                                        parent='test-topic-page')
    mock_get_page.assert_called_with(stub_measure_page.meta.guid)


def test_reject_page(test_app_client,
                     mock_user,
                     mock_get_page,
                     stub_topic_page,
                     stub_subtopic_page,
                     stub_measure_page,
                     mock_reject_page):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id
    test_app_client.get(url_for('cms.reject_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid,
                                measure=stub_measure_page.guid,
                                follow_redirects=True))
    mock_reject_page.assert_called_once_with(stub_measure_page.meta.uri)

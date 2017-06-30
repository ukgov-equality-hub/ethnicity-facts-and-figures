import datetime
import pytest

from flask import url_for
from bs4 import BeautifulSoup

from application.cms.forms import MeasurePageForm
from application.cms.models import DbPage
from application.cms.page_service import PageService

pytestmark = pytest.mark.usefixtures('mock_page_service_get_pages_by_type')


def test_create_measure_page(test_app_client,
                             mock_user,
                             stub_topic_page,
                             stub_subtopic_page,
                             stub_measure_form_data):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    stub_measure_form_data['publication_date'] = datetime.date.today()
    form = MeasurePageForm(**stub_measure_form_data)

    resp = test_app_client.post(url_for('cms.create_measure_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid), data=form.data, follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'created page %s' % stub_measure_form_data['title']


def test_reject_page(app,
                     test_app_client,
                     mock_user,
                     stub_topic_page,
                     stub_subtopic_page,
                     stub_measure_page):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id
    test_app_client.get(url_for('cms.reject_page',
                                topic=stub_topic_page.guid,
                                subtopic=stub_subtopic_page.guid,
                                measure=stub_measure_page.guid,
                                follow_redirects=True))
    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == 'REJECTED'

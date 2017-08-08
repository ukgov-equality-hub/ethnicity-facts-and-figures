from bs4 import BeautifulSoup
from flask import url_for

from application.cms.page_service import PageService

page_service = PageService()


def test_internal_user_can_see_page_regardless_of_state(test_app_client,
                                                        mock_user,
                                                        stub_topic_page,
                                                        stub_subtopic_page,
                                                        stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    assert stub_measure_page.status == 'DRAFT'

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test Measure Page'

    stub_measure_page.status = 'REJECTED'
    page_service.save_page(stub_measure_page)

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test Measure Page'


def test_departmental_user_cannot_see_page_unless_in_review(test_app_client,
                                                            mock_dept_user,
                                                            stub_topic_page,
                                                            stub_subtopic_page,
                                                            stub_measure_page):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_dept_user.id

    assert stub_measure_page.status == 'DRAFT'

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'This page is not ready to review'

    stub_measure_page.status = 'DEPARTMENT_REVIEW'
    page_service.save_page(stub_measure_page)

    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test Measure Page'

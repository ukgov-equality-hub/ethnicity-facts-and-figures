from bs4 import BeautifulSoup
from flask import url_for

from application.cms.page_service import PageService

page_service = PageService()


def test_internal_user_can_see_page_regardless_of_state(test_app_client,
                                                        db_session,
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
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test Measure Page'


def test_departmental_user_cannot_see_page_unless_in_review(test_app_client,
                                                            db_session,
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
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test Measure Page'


def test_get_file_download_returns_404(test_app_client,
                                       mock_user,
                                       stub_topic_page,
                                       stub_subtopic_page,
                                       stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('static_site.measure_page_file_download',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version,
                                       filename='nofile.csv'))

    assert resp.status_code == 404


def test_view_export_page(test_app_client,
                          db_session,
                          mock_user,
                          stub_topic_page,
                          stub_subtopic_page,
                          stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    assert stub_measure_page.status == 'DRAFT'

    resp = test_app_client.get(url_for('static_site.measure_page_markdown',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Title: Test Measure Page'


def test_view_topic_page(test_app_client, mock_user, stub_topic_page):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('static_site.topic', uri=stub_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test topic page'


def test_view_topic_page_in_static_mode_does_not_contain_reordering_javascript(test_app_client,
                                                                               mock_user,
                                                                               stub_topic_page):
        import re
        with test_app_client.session_transaction() as session:
            session['user_id'] = mock_user.id

        resp = test_app_client.get(url_for('static_site.topic', uri=stub_topic_page.uri))

        assert resp.status_code == 200
        page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
        assert page.h1.text.strip() == 'Test topic page'
        assert len(page.find_all('script', text=re.compile("setupReorderableTables"))) == 1

        resp = test_app_client.get(url_for('static_site.topic', uri=stub_topic_page.uri, static_mode=True))

        assert resp.status_code == 200
        page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
        assert page.h1.text.strip() == 'Test topic page'
        assert len(page.find_all('script', text=re.compile("setupReorderableTables"))) == 0


def test_view_index_page_only_contains_one_topic(test_app_client,
                                                 mock_user,
                                                 stub_home_page,
                                                 stub_topic_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('static_site.index'))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Ethnicity facts and figures'
    topics = page.find_all('div', class_='topics')
    assert len(topics) == 1
    topics[0].find('a').text.strip() == stub_topic_page.title


def test_view_sandbox_topic(test_app_client, mock_user, stub_sandbox_topic_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('static_site.topic', uri=stub_sandbox_topic_page.uri))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.h1.text.strip() == 'Test sandbox topic page'

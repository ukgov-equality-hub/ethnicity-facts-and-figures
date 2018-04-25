from datetime import datetime
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


def test_view_measure_page(test_app_client, mock_user, stub_topic_page, stub_subtopic_page, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('static_site.measure_page',
                                       topic=stub_topic_page.uri,
                                       subtopic=stub_subtopic_page.uri,
                                       measure=stub_measure_page.uri,
                                       version=stub_measure_page.version))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')

    assert page.h1.text.strip() == stub_measure_page.title

    # check metadata
    metadata_titles = page.find('div', class_='metadata').find_all('dt')
    assert len(metadata_titles) == 5
    assert metadata_titles[0].text == 'Department:'
    assert metadata_titles[1].text == 'Published:'
    assert metadata_titles[2].text == 'Source:'
    assert metadata_titles[3].text == 'Area covered:'
    assert metadata_titles[4].text == 'Time period:'

    metadata_values = page.find('div', class_='metadata').find_all('dd')
    assert len(metadata_titles) == 5
    assert metadata_values[0].text.strip() == 'Department for Work and Pensions'
    assert metadata_values[1].text.strip() == datetime.now().date().strftime('%d %B %Y')
    assert metadata_values[2].text.strip() == 'DWP Stats'
    assert metadata_values[3].text.strip() == 'UK'
    assert metadata_values[4].text.strip() == '4 months'

    things_to_know = page.find('span', attrs={'id': 'things-you-need-to-know'})
    assert things_to_know
    assert things_to_know.text.strip() == 'Things you need to know'

    what_measured = page.find('span', attrs={'id': 'what-the-data-measures'})
    assert what_measured
    assert what_measured.text.strip() == 'What the data measures'

    categories_used = page.find('span', attrs={'id': 'the-ethnic-categories-used-in-this-data'})
    assert categories_used
    assert categories_used.text.strip() == 'The ethnic categories used in this data'

    # check footer accordions
    methodology = page.find('h2', attrs={'id': 'methodology'})
    assert methodology
    assert methodology.text.strip() == 'Methodology'

    data_source_details = page.find('h2', attrs={'id': 'data-sources'})
    assert data_source_details
    assert data_source_details.text.strip() == 'Data sources'
    data_source_headings = data_source_details.parent.parent.find_all('h3')
    assert data_source_headings[0].text.strip() == 'Source'
    assert data_source_headings[1].text.strip() == 'Publisher'
    assert data_source_headings[2].text.strip() == 'Note on corrections or updates'
    assert data_source_headings[3].text.strip() == 'Publication frequency'
    assert data_source_headings[4].text.strip() == 'Purpose of data source'
    assert data_source_headings[5].text.strip() == 'Suppression rules and disclosure control'
    assert data_source_headings[6].text.strip() == 'Rounding'

    download_the_data = page.find('h2', attrs={'id': 'download-the-data'})
    assert download_the_data
    assert download_the_data.text.strip() == 'Download the data'

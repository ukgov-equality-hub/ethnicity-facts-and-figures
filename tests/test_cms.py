import pytest

from flask import url_for
from bs4 import BeautifulSoup

pytestmark = pytest.mark.usefixtures('mock_page_service_get_pages')


def test_create_measure_page(client, mock_user, mock_create_page, mock_get_page, stub_topic_page, stub_measure_page):

    with client.session_transaction() as session:
        session['user_id'] = mock_user.id

    form_data = {'title': stub_measure_page.title,
                 'location_definition_detail': stub_measure_page.location_definition_detail,
                 'location_definition_summary': stub_measure_page.location_definition_summary,
                 'measure_summary': stub_measure_page.measure_summary,
                 'estimation': stub_measure_page.estimation,
                 'qmi_text': stub_measure_page.qmi_text,
                 'need_to_know': stub_measure_page.need_to_know,
                 'contact_name': stub_measure_page.contact_name,
                 'contact_email': stub_measure_page.contact_email,
                 'contact_phone': stub_measure_page.contact_phone,
                 'summary': stub_measure_page.summary,
                 'data_type': stub_measure_page.data_type,
                 'frequency': stub_measure_page.frequency,
                 'ethnicity_definition_summary': stub_measure_page.ethnicity_definition_summary,
                 'qmi_url': stub_measure_page.qmi_url,
                 'guid': stub_measure_page.guid,
                 'time_covered': stub_measure_page.time_covered,
                 'geographic_coverage': stub_measure_page.geographic_coverage,
                 'department_source': stub_measure_page.department_source,
                 'ethnicity_definition_detail': stub_measure_page.ethnicity_definition_detail,
                 'methodology': stub_measure_page.methodology,
                 'population_or_sample': stub_measure_page.population_or_sample,
                 'keywords': stub_measure_page.keywords,
                 'published_date': stub_measure_page.published_date,
                 'next_update_date': stub_measure_page.published_date,
                 'quality_assurance': stub_measure_page.quality_assurance,
                 'last_update_date': stub_measure_page.last_update_date,
                 'revisions': stub_measure_page.revisions,
                 'source_text': stub_measure_page.source_text,
                 'source_url': stub_measure_page.source_url,
                 'disclosure_control': stub_measure_page.disclosure_control}

    resp = client.post(url_for('cms.create_measure_page',
                               topic_slug=stub_topic_page.guid),
                       data=form_data,
                       follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Created page %s' % stub_measure_page.title

    mock_create_page.assert_called_with(data=form_data,
                                        page_type='measure',
                                        parent='test-topic-page')
    mock_get_page.assert_called_with(stub_measure_page.meta.uri)


def test_reject_page(client, mock_user, mock_get_page, stub_topic_page, mock_reject_page):
    with client.session_transaction() as session:
        session['user_id'] = mock_user.id
    resp = client.get(url_for('cms.reject_page', slug=stub_topic_page.meta.uri), follow_redirects=True)
    assert resp.status_code == 200
    mock_reject_page.assert_called_once_with(stub_topic_page.meta.uri)

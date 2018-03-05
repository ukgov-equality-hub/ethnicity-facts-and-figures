from flask import url_for
from pytest_bdd import scenario, given, when, then

from application.cms.models import TypeOfData
from application.cms.page_service import PageService
from bs4 import BeautifulSoup

created_measure_url = None
created_measure_page = None


@scenario('features/life_cycle_of_measure_page.feature', 'Create a fresh measure page')
def test_create_measure_pages():
    print("Scenario: Create a fresh measure page")


given("a fresh cms with a topic page TestTopic with subtopic TestSubtopic", fixture="bdd_app")


@when('Editor creates a new measure page with name TestMeasure as a child of TestSubtopic')
def create_measure_page(bdd_app_client, bdd_app_editor):
    signin(bdd_app_editor, bdd_app_client)
    form_data = {'title': 'Test Measure'}
    response = bdd_app_client.post(url_for('cms.create_measure_page',
                                           topic='bdd_topic',
                                           subtopic='bdd_subtopic'),
                                   data=form_data)
    assert response.status_code == 302
    global created_measure_url
    created_measure_url = response.location


@then('a new measure page should exist with name TestMeasure with draft status')
def measure_page_does_exist(bdd_app_client):
    response = bdd_app_client.get(created_measure_url)
    global created_measure_page
    created_measure_page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert created_measure_page.find(id='title')['value'] == 'Test Measure'
    assert 'Draft' in created_measure_page.find_all('span', class_="info")[1].text


@scenario('features/life_cycle_of_measure_page.feature', 'Try to send an incomplete measure page to internal review')
def test_send_incomplete_to_internal_review():
    print("Scenario: Try to send an incomplete measure page to internal review")


@when('Editor tries to send incomplete TestMeasure page to Internal Review')
def attempt_send_to_internal_review(bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    send_to_review_url = created_measure_url.replace('edit', 'send-to-review')
    response = bdd_app_client.get(send_to_review_url, follow_redirects=True)
    global created_measure_page
    created_measure_page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')


@then('they get an error message saying page is not complete')
def editor_gets_sees_flash_error_message_displayed():
    global created_measure_page
    assert created_measure_page.find(id='title')['value'] == 'Test Measure'
    assert 'Cannot submit for review' in created_measure_page.find('div', class_="alert-box").text
    assert 'Draft' in created_measure_page.find_all('span', class_="info")[1].text


@scenario('features/life_cycle_of_measure_page.feature', 'Update a measure page')
def test_update_measure_pages():
    print("Scenario: Update a measure page")


@when('Editor updates some data on the TestMeasure page')
def update_measure_data(bdd_app, bdd_app_client, bdd_app_editor):
    signin(bdd_app_editor, bdd_app_client)

    form_data = measure_form_data(title='Test Measure',
                                  everything_else='update',
                                  db_version_id=1)

    global created_measure_url
    response = bdd_app_client.post(created_measure_url, data=form_data, follow_redirects=True)
    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Updated page "Test Measure"'


@then('the TestMeasure page should reload with the correct data')
def saved_data_does_reload(bdd_app, bdd_app_client):
    response = bdd_app_client.get(created_measure_url)
    global created_measure_page
    created_measure_page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    assert created_measure_page.find(id='title')['value'] == 'Test Measure'
    assert 'Draft' in created_measure_page.find_all('span', class_="info")[1].text

    assert created_measure_page.find(id='measure_summary').text == 'update'
    assert created_measure_page.find(id='estimation').text == 'update'
    assert created_measure_page.find(id='need_to_know').text == 'update'
    assert created_measure_page.find(id='time_covered')['value'] == 'update'
    assert created_measure_page.find(id='methodology').text == 'update'
    assert created_measure_page.find(id='data_source_purpose').text == 'update'
    assert created_measure_page.find(id='disclosure_control').text == 'update'
    assert created_measure_page.find(id='source_url')['value'] == 'update'
    # that's enough of this rubbish


@scenario('features/life_cycle_of_measure_page.feature', 'Send a completed page to internal review')
def test_send_completed_to_internal_review():
    print("Scenario: Send a completed page to internal review")


@when('Editor now sends completed TestMeasure page to review')
def completed_measure_page_to_review(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    send_to_review_url = created_measure_url.replace('edit', 'send-to-review')
    response = bdd_app_client.get(send_to_review_url, follow_redirects=True)
    global created_measure_page
    created_measure_page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')


@then('the status of TestMeasure is Internal Review')
def measure_page_status_is_internal_review(bdd_app):
    global created_measure_page
    assert 'Internal review' in created_measure_page.find_all('span', class_="info")[1].text.replace(u'\xa0', ' ')


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id


def measure_form_data(title, everything_else, db_version_id=1):
    return {'title': title,
            'measure_summary': everything_else,
            'estimation': everything_else,
            'qmi_text': everything_else,
            'need_to_know': everything_else,
            'contact_name': everything_else,
            'contact_email': everything_else,
            'contact_phone': everything_else,
            'summary': everything_else,
            'administrative_data': TypeOfData.ADMINISTRATIVE.name,
            'ethnicity_definition_summary': everything_else,
            'qmi_url': everything_else,
            'time_covered': everything_else,
            'england': 'y',
            'wales': 'y',
            'scotland': 'y',
            'northern_ireland': 'y',
            'department_source': 'D10',
            'ethnicity_definition_detail': everything_else,
            'methodology': everything_else,
            'keywords': everything_else,
            'published_date': everything_else,
            'next_update_date': everything_else,
            'quality_assurance': everything_else,
            'last_update_date': everything_else,
            'revisions': everything_else,
            'source_text': everything_else,
            'source_url': everything_else,
            'disclosure_control': everything_else,
            'data_source_purpose': everything_else,
            'lowest_level_of_geography_id': 'UK',
            'internal_edit_summary': everything_else,
            'db_version_id': db_version_id,
            'frequency': 'Quarterly',
            'frequency_id': 1,
            'type_of_statistic_id': 1
            }

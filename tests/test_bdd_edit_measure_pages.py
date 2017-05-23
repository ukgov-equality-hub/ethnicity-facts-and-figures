import pytest
from flask import url_for
from pytest_bdd import scenario, given, when, then

from application.cms.models import Meta, Page
from application.cms.page_service import PageService


@scenario('features/edit_measure_pages.feature', 'Create a fresh measure page with minimum fields')
def test_create_measure_page_with_minimum_fields():
    print("Scenario: Create a fresh measure page with minimum fields")


given("a fresh cms with a topic page TestTopic with subtopic TestSubtopic", fixture="test_app")

@when('I create a new measure page MeasurePage with minimum required fields')
def create_minimum_measure_page(test_app_editor, test_app_client):
    signin(test_app_editor, test_app_client)
    # post to create measure page endpoint (currently not working pending save without validation story)
    form_data = measure_form_data(title='Test Measure', guid='test-measure', everything_else='x')
    test_app_client.post(url_for('cms.create_measure_page', topic='testtopic', subtopic='testsubtopic'),
                         data=form_data, follow_redirects=True)


@then('measure page with minimum required fields is saved')
def measure_page_has_minimum_fields(test_app):
    # check the page is saved
    page = get_page_from_app(test_app, 'test-measure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'x'


@then('measure page is in draft')
def measure_page_has_minimum_fields(test_app):
    # check the page has status DRAFT
    page = get_page_from_app(test_app, 'test-measure')
    assert page.meta.status == "DRAFT"


@scenario('features/edit_measure_pages.feature', 'Update a measure page with default info')
def test_update_measure_page_with_default_info():
    pass

@when('I save default data on the MeasurePage page')
def save_default_data(test_app_editor, test_app_client):
    signin(test_app_editor, test_app_client)

    # post to update measure page endpoint
    form_data = measure_form_data(title='Test Measure', guid='test-measure', everything_else='update')
    test_app_client.post(url_for('cms.edit_measure_page', topic='testtopic', subtopic='testsubtopic', measure='test-measure'),
                         data=form_data, follow_redirects=True)


@then('the MeasurePage page should have default correct data')
def measure_page_has_default_fields(test_app):
    page = get_page_from_app(test_app, 'test-measure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'update'


@scenario('features/edit_measure_pages.feature', 'Upload a file')
def test_upload_a_file():
    print("Scenario: Upload a file")


@when('I upload a file to a page')
def upload_file_to_measure_page():
    print("I upload a file to a page")


@then('the MeasurePage page should have one upload listed')
def measure_page_should_have_one_upload_listed():
    print("the MeasurePage page should have one upload listed")


@then('the file should exist in page source folder')
def measure_page_should_have_file_in_data_source_folder():
    print("the file should exist in page source folder")


@then('the file should contain original data')
def measure_page_file_should_persist_data():
    print("the file should contain original data")


@scenario('features/edit_measure_pages.feature', 'Add a dimension to a measure page')
def test_add_a_dimension_to_a_measure_page():
    print("Scenario: Add a dimension to a measure page")


@when('I add a dimension to a measure page')
def add_a_dimension_to_a_measure_page():
    print("I add a dimension to a measure page")


@then('the MeasurePage page should have one dimension')
def measure_page_should_have_one_dimension():
    print("the MeasurePage page should have one dimension")


@scenario('features/edit_measure_pages.feature', 'Add chart to a dimension')
def test_add_a_chart_to_a_dimension():
    print("Scenario: Add chart to a dimension")


@when('I add a chart to a dimension')
def add_a_chart_to_a_dimension():
    print("I add a chart to a dimension")


@then('the dimension should have the chart data')
def dimension_has_chart_data():
    print("the dimension should have the chart data")


@then('the chart json should be saved in page source')
def chart_source_data_should_be_saved_in_source_directory():
    print("the chart source data should be saved in page source")


@scenario('features/edit_measure_pages.feature', 'Add table to a dimension')
def test_add_a_table_to_a_dimension():
    print("Scenario: Add table to a dimension")


@when('I add a table to a dimension')
def add_a_table_to_a_dimension():
    print("I add a chart to a dimension")


@then('the dimension should have the table data')
def dimension_has_table_data():
    print("the dimension should have the table data")


@then('the table json should be saved in page source')
def table_source_data_should_be_saved_in_source_directory():
    print("the table json should be saved in page source")


def get_page_from_app(from_app, page_guid):
    page_service = PageService()
    page_service.init_app(from_app)
    return page_service.get_page(page_guid)


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id


def measure_form_data(title, guid, everything_else):
    return {'title': title,
            'guid': guid,
            'location_definition_detail': everything_else, 'location_definition_summary': everything_else,
            'measure_summary': everything_else, 'estimation': everything_else,
            'qmi_text': everything_else, 'need_to_know': everything_else,
            'contact_name': everything_else, 'contact_email': everything_else, 'contact_phone': everything_else,
            'summary': everything_else, 'data_type': everything_else, 'frequency': everything_else,
            'ethnicity_definition_summary': everything_else, 'qmi_url': everything_else,
            'time_covered': everything_else, 'geographic_coverage': everything_else,
            'department_source': everything_else, 'ethnicity_definition_detail': everything_else,
            'methodology': everything_else, 'population_or_sample': everything_else,
            'keywords': everything_else, 'published_date': everything_else,
            'next_update_date': everything_else, 'quality_assurance': everything_else,
            'last_update_date': everything_else, 'revisions': everything_else,
            'source_text': everything_else, 'source_url': everything_else,
            'disclosure_control': everything_else}

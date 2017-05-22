import pytest
from pytest_bdd import scenario, given, when, then

from application.cms.page_service import PageService

@scenario('features/edit_measure_pages.feature', 'Create a fresh measure page with minimum fields')
def test_create_measure_page_with_minimum_fields():
    print("Scenario: Create a fresh measure page with minimum fields")


given("a fresh cms with a topic page TestTopic with subtopic TestTopic", fixture="fresh_app")

# def initialise_example_cms(app):
#     page_service = PageService()
#     page_service.init_app(app)
#     page_service.create_page(page_type='topic', parent='homepage', data={'guid':'TestTopic','title':'TestTopic'})
#     page_service.create_page(page_type='subtopic', parent='TestTopic',
#                              data={'guid':'TestSubtopic','title':'TestSubtopic'})


@when('I sign in as an internal user')
def sign_in_as_internal_user_alpha():
    print("I sign in as an internal user")


@when('I create a new measure page MeasurePage with minimum required fields')
def create_minimum_measure_page():
    print("I create a new measure page MeasurePage with minimum required fields")


@then('measure page with minimum required fields is saved')
def measure_page_has_minimum_fields():
    print("measure page with minimum required fields is saved")


@scenario('features/edit_measure_pages.feature', 'Update a measure page with default info')
def test_update_measure_page_with_default_info():
    print("Scenario: Update a measure page with default info")


@when('I save default data on the MeasurePage page')
def save_default_data():
    print("I save default data on the MeasurePage page")


@when('I reload the MeasurePage')
def reload_measure_page():
    print("I reload the MeasurePage")


@then('the MeasurePage page should have default correct data')
def measure_page_has_default_fields():
    print("the MeasurePage page should have default correct data")


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

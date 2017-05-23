from flask import url_for
from pytest_bdd import scenario, given, when, then
from application.cms.page_service import PageService


@scenario('features/life_cycle_of_measure_page.feature', 'Create a fresh measure page')
def test_create_measure_pages():
    print("Scenario: Create a fresh measure page")


given("a fresh cms with a topic page TestTopic with subtopic TestSubtopic", fixture="test_app")


@when('Editor creates a new measure page with name TestMeasure as a child of TestSubtopic')
def create_measure_page(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)
    # post to create measure page endpoint (currently not working pending save without validation story)
    form_data = measure_form_data(title='Test Measure', guid='testmeasure', everything_else='blank')
    test_app_client.post(url_for('cms.create_measure_page', topic='testtopic', subtopic='testsubtopic'),
                         data=form_data, follow_redirects=True)


@then('a new measure page should exist with name TestMeasure')
def measure_page_does_exist(test_app):
    # check the page is saved
    page = get_page_from_app(test_app, 'testmeasure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'blank'


@then('the status of measure page is draft')
def measure_page_has_minimum_fields(test_app):
    # check the page has status DRAFT
    page = get_page_from_app(test_app, 'testmeasure')
    assert page.meta.status == "DRAFT"


@then('the audit log should record that Editor created TestMeasure')
def audit_log_does_record_measure_create():
    # not yet implemented
    print("TODO: the audit log should record that I have created TestMeasure")


@then('TestMeasure is internal access only')
def check_internal_access_only():
    print('TODO: Check internal access - Implement when roles exist')


@then('TestMeasure is internal and external access')
def check_internal_and_external():
    print('TODO: Check internal and external access - Implement when roles exist')


@scenario('features/life_cycle_of_measure_page.feature', 'Update a measure page')
def test_update_measure_pages():
    print("Scenario: Update a measure page")


@when('Editor updates some data on the TestMeasure page')
def update_measure_data(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)

    # post to update measure page endpoint
    form_data = measure_form_data(title='Test Measure', guid='testmeasure', everything_else='update')
    test_app_client.post(url_for('cms.edit_measure_page', topic='testtopic',
                                 subtopic='testsubtopic', measure='testmeasure'),
                         data=form_data, follow_redirects=True)


@then('the TestMeasure page should reload with the correct data')
def saved_data_does_reload(test_app):
    page = get_page_from_app(test_app, 'testmeasure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'update'


@then('the audit log should record that Editor saved TestMeasure')
def audit_log_does_record_measure_update():
    print("TODO: the audit log should record that I have saved TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Try to send an incomplete measure page to internal review')
def test_send_incomplete_to_internal_review():
    print("Scenario: Try to send an incomplete measure page to internal review")


@when('Editor tries to send incomplete TestMeasure page to Internal Review')
def attempt_send_to_internal_review():
    print("TODO: I try to send the TestMeasure page to Internal Review without completing all fields")


@scenario('features/life_cycle_of_measure_page.feature', 'Send a page to internal review')
def test_send_completed_to_internal_review():
    print("Scenario: Send a page to internal review")


@when('Editor completes all fields on the TestMeasure page')
def complete_measure_page():
    print("I complete all fields on the TestMeasure page")


@when('Editor sends the TestMeasure page to Internal Review')
def send_to_internal_review():
    print("TODO: I try to send the TestMeasure page to Internal Review without completing all fields")


@then('the status of TestMeasure changes to Internal Review')
def measure_page_status_is_internal_review():
    print("Measure page status is internal review")


@then('the audit log should record that Editor submitted TestMeasure to internal review')
def audit_log_does_record_submit_to_internal_review():
    print("the audit log should record that I have submitted TestMeasure to internal review")


@scenario('features/life_cycle_of_measure_page.feature', 'Page rejected at internal review')
def test_internal_reviewer_rejects_page_at_internal_review():
    print("Scenario: Page rejected at internal review")


@when('Reviewer rejects the TestMeasure page at internal review')
def reject_measure_page():
    print("I reject the TestMeasure page")


@then('the status of TestMeasure page changes to rejected')
def measure_page_status_is_rejected():
    print("the status of TestMeasure page is rejected")


@then('the audit log should record that Reviewer rejected TestMeasure')
def audit_log_does_record_reject_page():
    print("the audit log should record that I have rejected TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Rejected page is updated')
def test_internal_editor_updates_rejected_page():
    print("Scenario: Rejected page is updated")


@when('Editor makes changes to the rejected TestMeasure page')
def change_rejected_test_measure_page():
    print("I make changes to the TestMeasure page")


@then('the rejected TestMeasure page should be updated')
def measure_page_status_is_rejected():
    print("the status of TestMeasure page is rejected")


@then('the audit log should record that Editor updated the rejected TestMeasure')
def audit_log_does_record_update_rejected_page():
    print("the audit log records that I have updated rejected TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Resubmit rejected page')
def test_internal_editor_resubmits_page():
    print("Scenario: Resubmit rejected page")


@scenario('features/life_cycle_of_measure_page.feature', 'Accept page at internal review')
def test_internal_reviewer_accepts_page():
    print("Scenario: Accept page at internal review")


@when('Reviewer accepts the TestMeasure page')
def accept_test_measure_page():
    print("I accept the TestMeasure page")


@then('the status of TestMeasure page changes to departmental review')
def measure_page_status_is_departmental_review():
    print("the status of TestMeasure page is departmental review")


@then('the audit log should record that Reviewer accepted TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("the audit log should record that I have accepted TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Departmental user rejects page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('Department rejects the TestMeasure page at departmental review')
def reject_test_measure_page():
    print("I reject the TestMeasure page at departmental review")


@then('the audit log should record that Department rejected TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("the audit log should record that I have accepted TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Update a measure page after departmental rejection')
def test_update_rejected_page_after_department_rejection():
    print("Scenario: Update a measure page after departmental rejection")


@when('Editor makes changes to the departmental rejected TestMeasure page')
def change_department_rejected_test_measure_page():
    print("I make changes to the departmental rejected TestMeasure page")


@then('the departmental rejected TestMeasure should be updated')
def measure_page_is_updated_after_department_rejection():
    print("the departmental rejected TestMeasure should be updated")


@then('the audit log should record that Editor updated department rejected TestMeasure')
def audit_log_does_record_update_department_rejected_page():
    print("the audit log records that I have updated rejected TestMeasure")


@scenario('features/life_cycle_of_measure_page.feature', 'Resubmit page rejected at departmental review')
def test_resubmit_page_rejected_at_internal_review():
    print("Scenario: Resubmit page rejected at internal review")


@scenario('features/life_cycle_of_measure_page.feature',
          'Internal reviewer accepts page previously rejected at internal review')
def test_departmental_user_rejects_page():
    print("Scenario: Internal reviewer accepts page previously rejected at internal review")


@scenario('features/life_cycle_of_measure_page.feature', 'Departmental user accepts page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('Department accepts the TestMeasure page at departmental review')
def accept_test_measure_page():
    print("I accept the TestMeasure page at departmental review")


@then('the status of TestMeasure page changes to publish')
def measure_page_status_is_publish():
    print("the status of TestMeasure page changes to publish")


@then('the audit log should record that Department accepted TestMeasure for publish')
def audit_log_does_record_accept_page_for_publish():
    print("the audit log should record that I have accepted TestMeasure for publish")


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

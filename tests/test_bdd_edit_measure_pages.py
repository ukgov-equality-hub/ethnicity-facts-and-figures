from pytest_bdd import scenario, given, when, then


@scenario('features/edit_measure_pages.feature', 'Create a fresh measure page')
def test_create_measure_pages():
    print("Scenario: Create a fresh measure page")


@given("a fresh cms with a topic page TestTopic with subtopic TestTopic")
def initialise_example_cms():
    print("a fresh cms with a topic page TestTopic with subtopic TestTopic")


@when('I sign in as an internal user')
def sign_in_as_internal_user_alpha():
    print("I sign in as an internal user")


@when('I create a new measure page with name TestMeasure as a child of TestSubtopic')
def create_measure_page():
    print("I create a new measure page with name TestMeasure as a child of TestSubtopic")


@then('a new measure page should exist with name TestMeasure')
def measure_page_does_exist():
    print("a new measure page should exist with name TestMeasure")


@then('TestMeasure should have parent TestSubtopic')
def measure_page_has_correct_parent():
    print("TestMeasure should have parent TestSubtopic")


@then('the audit log should record that I have created TestMeasure')
def audit_log_does_record_measure_create():
    print("the audit log should record that I have created TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Update a measure page')
def test_update_measure_pages():
    print("Scenario: Update a measure page")


@when('I save some data on the TestMeasure page')
def save_measure_data():
    print("I save some data on the TestMeasure page")


@then('the TestMeasure page should reload with the correct data')
def saved_data_does_reload():
    print("the TestMeasure page should reload with the correct data")


@then('the audit log should record that I have saved TestMeasure')
def audit_log_does_record_measure_update():
    print("the audit log should record that I have saved TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Try to send an incomplete measure page to internal review')
def test_send_incomplete_to_internal_review():
    print("Scenario: Try to send an incomplete measure page to internal review")


@when('I try to send the TestMeasure page to Internal Review without completing all fields')
@when('I send the TestMeasure page to Internal Review')
def attempt_send_to_internal_review():
    print("I try to send the TestMeasure page to Internal Review without completing all fields")


@then('I am not allowed to submit to Internal Review')
def measure_page_status_is_draft():
    print("Measure page status is draft")


@scenario('features/edit_measure_pages.feature', 'Send a page to internal review')
def test_send_completed_to_internal_review():
    print("Scenario: Send a page to internal review")


@when('I complete all fields on the TestMeasure page')
def complete_measure_page():
    print("I complete all fields on the TestMeasure page")


@then('the status of TestMeasure changes to Internal Review')
def measure_page_status_is_internal_review():
    print("Measure page status is internal review")


@then('the audit log should record that I have submitted TestMeasure to internal review')
def audit_log_does_record_submit_to_internal_review():
    print("the audit log should record that I have submitted TestMeasure to internal review")


@scenario('features/edit_measure_pages.feature', 'Departmental user accesses pages in internal review')
def test_departmental_user_access_pages_in_internal_review():
    print("Scenario: Departmental user accesses pages in internal review")


@given('a departmental user')
def create_department_user():
    print("given a departmental user")


@when('I sign in as departmental user')
def sign_in_departmental_user():
    print("I sign in as departmental user")


@then('I cannot access the TestMeasure page')
def access_to_measure_page_rejected():
    print("I cannot access the TestMeasure page")


@scenario('features/edit_measure_pages.feature', 'Internal reviewer accesses pages in internal review')
def test_internal_reviewer_user_access_pages_in_internal_review():
    print("Scenario: Internal reviewer accesses pages in internal review")


@given('an internal reviewer')
def create_reviewer():
    print("given an internal reviewer")


@when('I sign in as internal reviewer')
def sign_in_departmental_user():
    print("I sign in as internal reviewer")


@then('I can access the TestMeasure page')
def access_to_measure_page_allowed():
    print("I can access the TestMeasure page")


@scenario('features/edit_measure_pages.feature', 'Page rejected at internal review')
def test_internal_reviewer_rejects_page_at_internal_review():
    print("Scenario: Page rejected at internal review")


@when('I reject the TestMeasure page at internal review')
def reject_measure_page():
    print("I reject the TestMeasure page")


@then('the status of TestMeasure page changes to rejected')
def measure_page_status_is_rejected():
    print("the status of TestMeasure page is rejected")


@then('the audit log should record that I have rejected TestMeasure')
def audit_log_does_record_reject_page():
    print("the audit log should record that I have rejected TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Rejected page is updated')
def test_internal_editor_updates_rejected_page():
    print("Scenario: Rejected page is updated")


@when('I sign in as internal editor')
def sign_in_as_internal_editor():
    print("I sign in as internal editor")


@when('I make changes to the rejected TestMeasure page')
def change_rejected_test_measure_page():
    print("I make changes to the TestMeasure page")


@then('the rejected TestMeasure page should be updated')
def measure_page_status_is_rejected():
    print("the status of TestMeasure page is rejected")


@then('the audit log should record that I have updated rejected TestMeasure')
def audit_log_does_record_update_rejected_page():
    print("the audit log records that I have updated rejected TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Resubmit rejected page')
def test_internal_editor_resubmits_page():
    print("Scenario: Resubmit rejected page")


@scenario('features/edit_measure_pages.feature', 'Accept page at internal review')
def test_internal_reviewer_accepts_page():
    print("Scenario: Accept page at internal review")


@when('I accept the TestMeasure page')
def accept_test_measure_page():
    print("I accept the TestMeasure page")


@then('the status of TestMeasure page changes to departmental review')
def measure_page_status_is_departmental_review():
    print("the status of TestMeasure page is departmental review")


@then('the audit log should record that I have accepted TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("the audit log should record that I have accepted TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Departmental user accesses pages in departmental review')
def test_departmental_user_accesses_page_in_internal_review():
    print("Scenario: Departmental user accesses pages in departmental review")


@scenario('features/edit_measure_pages.feature', 'Departmental user rejects page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('I reject the TestMeasure page at departmental review')
def reject_test_measure_page():
    print("I reject the TestMeasure page at departmental review")


@then('the audit log should record that I have accepted TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("the audit log should record that I have accepted TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Departmental user accesses pages in departmental review')
def test_departmental_user_accesses_page_in_internal_review():
    print("Scenario: Departmental user accesses pages in departmental review")


@scenario('features/edit_measure_pages.feature', 'Departmental user rejects page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('I reject the TestMeasure page at departmental review')
def reject_test_measure_page():
    print("I reject the TestMeasure page at departmental review")


@scenario('features/edit_measure_pages.feature', 'Update a measure page after departmental rejection')
def test_update_rejected_page_after_department_rejection():
    print("Scenario: Update a measure page after departmental rejection")


@when('I make changes to the departmental rejected TestMeasure page')
def change_department_rejected_test_measure_page():
    print("I make changes to the departmental rejected TestMeasure page")


@then('the departmental rejected TestMeasure should be updated')
def measure_page_is_updated_after_department_rejection():
    print("the departmental rejected TestMeasure should be updated")


@then('the audit log should record that I have updated department rejected TestMeasure')
def audit_log_does_record_update_department_rejected_page():
    print("the audit log records that I have updated rejected TestMeasure")


@scenario('features/edit_measure_pages.feature', 'Resubmit page rejected at internal review')
def test_resubmit_page_rejected_at_internal_review():
    print("Scenario: Resubmit page rejected at internal review")


@scenario('features/edit_measure_pages.feature', 'Internal reviewer accepts page previously rejected at internal review')
def test_departmental_user_rejects_page():
    print("Scenario: Internal reviewer accepts page previously rejected at internal review")


@scenario('features/edit_measure_pages.feature', 'Departmental user accepts page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('I accept the TestMeasure page at departmental review')
def accept_test_measure_page():
    print("I accept the TestMeasure page at departmental review")


@then('the status of TestMeasure page changes to publish')
def measure_page_status_is_publish():
    print("the status of TestMeasure page changes to publish")


@then('the audit log should record that I have accepted TestMeasure for publish')
def audit_log_does_record_accept_page_for_publish():
    print("the audit log should record that I have accepted TestMeasure for publish")

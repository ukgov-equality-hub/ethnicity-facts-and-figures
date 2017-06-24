from flask import url_for
from pytest_bdd import scenario, given, when, then
from application.cms.page_service import PageService


@scenario('features/life_cycle_of_measure_page.feature', 'Create a fresh measure page')
def test_create_measure_pages():
    print("Scenario: Create a fresh measure page")


given("a fresh cms with a topic page TestTopic with subtopic TestSubtopic", fixture="bdd_app")


@when('Editor creates a new measure page with name TestMeasure as a child of TestSubtopic')
def create_measure_page(bdd_app_client, bdd_app_editor):
    signin(bdd_app_editor, bdd_app_client)
    # post to create measure page endpoint (currently not working pending save without validation story)
    form_data = measure_form_data(title='Test Measure', guid='bdd_measure', everything_else='blank')
    bdd_app_client.post(url_for('cms.create_measure_page', topic='bdd_topic', subtopic='bdd_subtopic'),
                         data=form_data, follow_redirects=True)


@then('a new measure page should exist with name TestMeasure')
def measure_page_does_exist(bdd_app):
    # check the page is saved
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'blank'


@then('the status of TestMeasure page is draft')
def measure_page_has_minimum_fields(bdd_app):
    # check the page has status DRAFT
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "DRAFT"


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
def update_measure_data(bdd_app_client, bdd_app_editor):
    signin(bdd_app_editor, bdd_app_client)

    # post to update measure page endpoint
    form_data = measure_form_data(title='Test Measure', guid='bdd_measure', everything_else='update')
    bdd_app_client.post(url_for('cms.edit_measure_page', topic='bdd_topic',
                                 subtopic='bdd_subtopic', measure='bdd_measure'),
                         data=form_data, follow_redirects=True)


@then('the TestMeasure page should reload with the correct data')
def saved_data_does_reload(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'update'


@then('the audit log should record that Editor saved TestMeasure')
def audit_log_does_record_measure_update():
    print("TODO: the audit log should record that I have saved TestMeasure")


'''
--- This scenario is currently waiting on the part validation story to be completed
'''


@scenario('features/life_cycle_of_measure_page.feature', 'Try to send an incomplete measure page to internal review')
def test_send_incomplete_to_internal_review():
    print("Scenario: Try to send an incomplete measure page to internal review")


@when('Editor tries to send incomplete TestMeasure page to Internal Review')
def attempt_send_to_internal_review():
    print("TODO: I try to send the TestMeasure page to Internal Review without completing all fields")


'''
--- End
'''


@scenario('features/life_cycle_of_measure_page.feature', 'Send a page to internal review')
def test_send_completed_to_internal_review():
    print("Scenario: Send a page to internal review")


@when('Editor completes all fields on the TestMeasure page')
def complete_measure_page(bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)

    # post to update measure page endpoint
    form_data = measure_form_data(title='Test Measure', guid='bdd_measure', everything_else='complete')
    bdd_app_client.post(url_for('cms.edit_measure_page', topic='bdd_topic',
                                 subtopic='bdd_subtopic', measure='bdd_measure'),
                         data=form_data, follow_redirects=True)


@when('Editor sends the TestMeasure page to Internal Review')
def send_to_internal_review(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "DRAFT" or page.status == "REJECTED"
    bdd_app_client.get(url_for('cms.publish_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure'), follow_redirects=True)


@then('the status of TestMeasure is Internal Review')
def measure_page_status_is_internal_review(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "INTERNAL_REVIEW"


@then('the audit log should record that Editor submitted TestMeasure to internal review')
def audit_log_does_record_submit_to_internal_review():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Page rejected at internal review')
def test_internal_reviewer_rejects_page_at_internal_review():
    print("Scenario: Page rejected at internal review")


@when('Reviewer rejects the TestMeasure page at internal review')
def reject_measure_page(bdd_app, bdd_app_client, bdd_app_reviewer):
    signin(bdd_app_reviewer, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "INTERNAL_REVIEW"
    bdd_app_client.get(url_for('cms.reject_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure'), follow_redirects=True)


@then('the status of TestMeasure page is rejected')
def measure_page_status_is_rejected(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "REJECTED"


@then('the audit log should record that Reviewer rejected TestMeasure')
def audit_log_does_record_reject_page():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Rejected page is updated')
def test_internal_editor_updates_rejected_page():
    print("Scenario: Rejected page is updated")


@when('Editor makes changes to the rejected TestMeasure page')
def change_rejected_test_measure_page(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    # post to update measure page endpoint
    assert page.status == "REJECTED"
    form_data = measure_form_data(title='Test Measure', guid='bdd_measure',
                                  everything_else='update after internal reject')
    bdd_app_client.post(url_for('cms.edit_measure_page', topic='bdd_topic',
                                 subtopic='bdd_subtopic', measure='bdd_measure'),
                         data=form_data, follow_redirects=True)


@then('the rejected TestMeasure page should be updated')
def measure_page_status_is_updated(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.measure_summary == 'update after internal reject'


@then('the audit log should record that Editor updated the rejected TestMeasure')
def audit_log_does_record_update_rejected_page():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Resubmit rejected page')
def test_internal_editor_resubmits_page():
    print("Scenario: Resubmit rejected page")


@scenario('features/life_cycle_of_measure_page.feature', 'Accept page at internal review')
def test_internal_reviewer_accepts_page():
    print("Scenario: Accept page at internal review")


@when('Reviewer accepts the TestMeasure page')
def accept_test_measure_page(bdd_app, bdd_app_reviewer, bdd_app_client):
    signin(bdd_app_reviewer, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "INTERNAL_REVIEW"
    bdd_app_client.get(url_for('cms.publish_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure'), follow_redirects=True)


@then('the status of TestMeasure page is departmental review')
def measure_page_status_is_departmental_review(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "DEPARTMENT_REVIEW"


@then('the audit log should record that Reviewer accepted TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Departmental user rejects page in departmental review')
def test_departmental_user_rejects_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('Department rejects the TestMeasure page at departmental review')
def reject_test_measure_page(bdd_app, bdd_app_reviewer, bdd_app_client):
    # we have now changed this to internal users doing the whole rejection process (department can view only)
    signin(bdd_app_reviewer, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "DEPARTMENT_REVIEW"
    bdd_app_client.get(url_for('cms.reject_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure'), follow_redirects=True)


@then('the audit log should record that Department rejected TestMeasure')
def audit_log_does_record_accept_page_at_internal_review():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Update a measure page after departmental rejection')
def test_update_rejected_page_after_department_rejection():
    print("Scenario: Update a measure page after departmental rejection")


@when('Editor makes changes to the departmental rejected TestMeasure page')
def change_department_rejected_test_measure_page(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    # post to update measure page endpoint
    assert page.status == "REJECTED"
    form_data = measure_form_data(title='Test Measure', guid='bdd_measure',
                                  everything_else='update after department reject')
    bdd_app_client.post(url_for('cms.edit_measure_page', topic='bdd_topic',
                                 subtopic='bdd_subtopic', measure='bdd_measure'),
                         data=form_data, follow_redirects=True)


@then('the departmental rejected TestMeasure should be updated')
def measure_page_is_updated_after_department_rejection(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.measure_summary == 'update after department reject'


@then('the audit log should record that Editor updated department rejected TestMeasure')
def audit_log_does_record_update_department_rejected_page():
    print("TODO: Audit log")


@scenario('features/life_cycle_of_measure_page.feature', 'Resubmit page rejected at departmental review')
def test_resubmit_page_rejected_at_departmental_review():
    print("Scenario: Resubmit page rejected at internal review")


@scenario('features/life_cycle_of_measure_page.feature',
          'Internal reviewer accepts page previously rejected at departmental review')
def test_internal_user_accepts_department_rejected_page():
    print("Scenario: Internal reviewer accepts page previously rejected at internal review")


@scenario('features/life_cycle_of_measure_page.feature', 'Departmental user accepts page in departmental review')
def test_departmental_user_accepts_page():
    print("Scenario: Departmental user rejects page in departmental review")


@when('Department accepts the TestMeasure page at departmental review')
def department_accepts_test_measure_page(bdd_app, bdd_app_reviewer, bdd_app_client):
    # we have changed this process so that internal users do the final acceptance
    signin(bdd_app_reviewer, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "DEPARTMENT_REVIEW"
    bdd_app_client.get(url_for('cms.publish_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure'), follow_redirects=True)


@then('the status of TestMeasure page is accepted')
def measure_page_status_is_accepted(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "ACCEPTED"


@then('the audit log should record that Department accepted TestMeasure for publish')
def audit_log_does_record_accept_page_for_publish():
    print("TODO: Audit log")


def get_page_from_app(from_app, page_guid):
    return PageService().get_page(page_guid)


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id


def measure_form_data(title, guid, everything_else):
    return {'title': title,
            'guid': guid,
            'measure_summary': everything_else, 'estimation': everything_else,
            'qmi_text': everything_else, 'need_to_know': everything_else,
            'contact_name': everything_else, 'contact_email': everything_else, 'contact_phone': everything_else,
            'summary': everything_else, 'data_type': everything_else, 'frequency': everything_else,
            'ethnicity_definition_summary': everything_else, 'qmi_url': everything_else,
            'time_covered': everything_else, 'geographic_coverage': everything_else,
            'department_source': everything_else, 'ethnicity_definition_detail': everything_else,
            'methodology': everything_else,
            'keywords': everything_else, 'published_date': everything_else,
            'next_update_date': everything_else, 'quality_assurance': everything_else,
            'last_update_date': everything_else, 'revisions': everything_else,
            'source_text': everything_else, 'source_url': everything_else,
            'disclosure_control': everything_else,
            'data_source_purpose': everything_else,
            'lowest_level_of_geography': everything_else}

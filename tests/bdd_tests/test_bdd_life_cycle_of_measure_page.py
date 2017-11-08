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


@scenario('features/life_cycle_of_measure_page.feature', 'Update a measure page')
def test_update_measure_pages():
    print("Scenario: Update a measure page")


@when('Editor updates some data on the TestMeasure page')
def update_measure_data(bdd_app, bdd_app_client, bdd_app_editor):
    signin(bdd_app_editor, bdd_app_client)

    page = get_page_from_app(bdd_app, 'bdd_measure')
    form_data = measure_form_data(title='Test Measure',
                                  guid='bdd_measure',
                                  everything_else='update',
                                  db_version_id=page.db_version_id)

    bdd_app_client.post(url_for('cms.edit_measure_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure',
                                version='1.0'),
                        data=form_data, follow_redirects=True)


@then('the TestMeasure page should reload with the correct data')
def saved_data_does_reload(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page is not None
    assert page.title == 'Test Measure'
    assert page.measure_summary == 'update'

# '''
# --- This scenario is currently waiting on the part validation story to be completed
# '''
#
#
# @scenario('features/life_cycle_of_measure_page.feature', 'Try to send an incomplete measure page to internal review')
# def test_send_incomplete_to_internal_review():
#     print("Scenario: Try to send an incomplete measure page to internal review")
#
#
# @when('Editor tries to send incomplete TestMeasure page to Internal Review')
# def attempt_send_to_internal_review():
#     print("TODO: I try to send the TestMeasure page to Internal Review without completing all fields")
#
#
# '''
# --- End
# '''


@scenario('features/life_cycle_of_measure_page.feature', 'Send a page to internal review')
def test_send_completed_to_internal_review():
    print("Scenario: Send a page to internal review")


@when('Editor completes all fields on the TestMeasure page')
def complete_measure_page(bdd_app, bdd_app_editor, bdd_app_client):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    signin(bdd_app_editor, bdd_app_client)
    form_data = measure_form_data(title='Test Measure',
                                  guid='bdd_measure',
                                  everything_else='complete',
                                  db_version_id=page.db_version_id)
    bdd_app_client.post(url_for('cms.edit_measure_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure',
                                version='1.0'),
                        data=form_data, follow_redirects=True)


@when('Editor sends the TestMeasure page to Internal Review')
def send_to_internal_review(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    assert page.status == "DRAFT" or page.status == "REJECTED"
    bdd_app_client.get(url_for('cms.send_to_review',
                               topic='bdd_topic',
                               subtopic='bdd_subtopic',
                               measure='bdd_measure',
                               version='1.0'), follow_redirects=True)


@then('the status of TestMeasure is Internal Review')
def measure_page_status_is_internal_review(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "INTERNAL_REVIEW"


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
                               measure='bdd_measure',
                               version='1.0'), follow_redirects=True)


@then('the status of TestMeasure page is rejected')
def measure_page_status_is_rejected(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "REJECTED"


@scenario('features/life_cycle_of_measure_page.feature', 'Rejected page is updated')
def test_internal_editor_updates_rejected_page():
    print("Scenario: Rejected page is updated")


@when('Editor makes changes to the rejected TestMeasure page')
def change_rejected_test_measure_page(bdd_app, bdd_app_editor, bdd_app_client):
    signin(bdd_app_editor, bdd_app_client)
    page = get_page_from_app(bdd_app, 'bdd_measure')

    # post to update measure page endpoint
    assert page.status == "REJECTED"
    form_data = measure_form_data(title='Test Measure',
                                  guid='bdd_measure',
                                  everything_else='update after internal reject',
                                  db_version_id=page.db_version_id)

    bdd_app_client.post(url_for('cms.edit_measure_page',
                                topic='bdd_topic',
                                subtopic='bdd_subtopic',
                                measure='bdd_measure',
                                version='1.0'),
                        data=form_data, follow_redirects=True)


@then('the rejected TestMeasure page should be updated')
def measure_page_status_is_updated(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.measure_summary == 'update after internal reject'


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
    bdd_app_client.get(url_for('cms.send_to_review',
                               topic='bdd_topic',
                               subtopic='bdd_subtopic',
                               measure='bdd_measure',
                               version='1.0'), follow_redirects=True)


@then('the status of TestMeasure page is departmental review')
def measure_page_status_is_departmental_review(bdd_app):
    page = get_page_from_app(bdd_app, 'bdd_measure')
    assert page.status == "DEPARTMENT_REVIEW"


def get_page_from_app(from_app, page_guid):
    page_service = PageService()
    page_service.init_app(from_app)
    return page_service.get_page(page_guid)


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id


def measure_form_data(title, guid, everything_else, db_version_id=1):
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
            'lowest_level_of_geography': everything_else,
            'internal_edit_summary': everything_else,
            'db_version_id': db_version_id
            }

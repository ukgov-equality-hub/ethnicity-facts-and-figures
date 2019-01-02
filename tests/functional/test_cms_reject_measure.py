import pytest

from tests.functional.utils import (
    EXPECTED_STATUSES,
    create_measure_starting_at_topic_page,
    navigate_to_topic_page,
    login,
)

pytestmark = pytest.mark.usefixtures("app", "db_session", "stub_measure_page")

"""

THIS TEST MAKES SURE THAT MEASURES CAN BE REJECTED WHILE UNDER REVIEW

"""


def test_can_reject_a_measure_in_review_as_editor(
    driver,
    test_app_editor,
    test_app_admin,
    live_server,
    stub_topic_page,
    stub_subtopic_page,
    stub_published_measure_page,
):
    # GIVEN a setup with Topic and Subtopic
    login(driver, live_server, test_app_editor)
    navigate_to_topic_page(driver, live_server, stub_topic_page)

    # WHEN an editor creates and saves a new measure page
    measure_edit_page, page = create_measure_starting_at_topic_page(
        driver, live_server, stub_subtopic_page, stub_topic_page
    )

    # THEN the status should be draft
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["draft"]

    # WHEN we save and send it to internal review
    measure_edit_page.click_save_and_send_to_review()

    # THEN the status should be internal review
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["internal_review"]

    # WHEN we reject the page
    measure_edit_page.click_reject()

    # THEN the status should be rejected
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["rejected"]

    # WHEN we send it back to a draft
    measure_edit_page.click_send_back_to_draft()

    # THEN the status should be draft
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["draft"]

    # WHEN we save and send it for department review
    measure_edit_page.click_save_and_send_to_review()
    measure_edit_page.click_department_review()

    # THEN the status should be department review
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["department_review"]

    # WHEN we reject the measure again
    measure_edit_page.click_reject()

    # THEN the status should be rejected
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["rejected"]

    measure_edit_page.log_out()

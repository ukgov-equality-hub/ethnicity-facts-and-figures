import pytest

from tests.functional.utils import (
    EXPECTED_STATUSES,
    create_measure_starting_at_topic_page,
    navigate_to_topic_page,
    navigate_to_edit_page,
    login,
)

pytestmark = pytest.mark.usefixtures("app", "db_session", "stub_measure_page")

"""

THIS TEST WALKS THROUGH THE MEASURE LIFECYCLE

"""


def test_create_a_measure_as_editor(
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

    measure_edit_page.click_save_and_send_to_review()

    # THEN the status should be internal review
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["internal_review"]

    # WHEN we send page to department review
    measure_edit_page.click_department_review()

    # THEN the status should be department review
    driver.implicitly_wait(2)
    assert measure_edit_page.is_current()
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["department_review"]

    # AND the approve button should not be on page
    assert measure_edit_page.approved_is_visible() is False

    # GIVEN the department link
    review_link = measure_edit_page.get_review_link()

    # WHEN we log out and go to the review link
    measure_edit_page.log_out()
    driver.get(review_link)

    # THEN the preview page ought to have content
    assert page.title in driver.page_source

    # GIVEN the admin user
    login(driver, live_server, test_app_admin)

    # WHEN we go to the edit page
    navigate_to_edit_page(driver, live_server, stub_topic_page, stub_subtopic_page, page)

    # THEN the approve button is visible
    assert measure_edit_page.approved_is_visible() is True

    # WHEN the admin user clicks approve
    measure_edit_page.click_approved()

    # THEN the status should be published
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["published"]

    measure_edit_page.log_out()

import random

from application.auth.models import TypeOfUser

from tests.functional.utils import (
    EXPECTED_STATUSES,
    create_measure_starting_at_topic_page,
    navigate_to_topic_page,
    navigate_to_edit_page,
    driver_login,
)
from tests.models import UserFactory, MeasureVersionFactory, DataSourceFactory

"""

THIS TEST WALKS THROUGH THE MEASURE LIFECYCLE

"""


def test_create_a_measure_as_editor(driver, live_server, government_departments, frequencies_of_release):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER, active=True)
    approved_measure_version = MeasureVersionFactory(
        status="APPROVED",
        data_sources__publisher=random.choice(government_departments),
        data_sources__frequency_of_release=random.choice(frequencies_of_release),
    )
    sample_measure_version = MeasureVersionFactory.build(data_sources=[])
    sample_data_source = DataSourceFactory.build(
        publisher__name=random.choice(government_departments).name,
        frequency_of_release__description=random.choice(frequencies_of_release).description,
    )

    # GIVEN a setup with Topic and Subtopic
    driver_login(driver, live_server, rdu_user)
    navigate_to_topic_page(driver, live_server, approved_measure_version.measure.subtopic.topic)

    # WHEN an editor creates and saves a new measure page
    measure_edit_page, page = create_measure_starting_at_topic_page(
        driver,
        live_server,
        approved_measure_version.measure.subtopic.topic,
        approved_measure_version.measure.subtopic,
        sample_measure_version,
        sample_data_source,
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
    driver_login(driver, live_server, admin_user)

    # WHEN we go to the edit page
    navigate_to_edit_page(
        driver,
        live_server,
        approved_measure_version.measure.subtopic.topic,
        approved_measure_version.measure.subtopic,
        page,
    )

    # THEN the approve button is visible
    assert measure_edit_page.approved_is_visible() is True

    # WHEN the admin user clicks approve
    measure_edit_page.click_approved()

    # THEN the status should be published
    assert measure_edit_page.get_status() == EXPECTED_STATUSES["published"]

    measure_edit_page.log_out()

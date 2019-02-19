import random

from application.auth.models import TypeOfUser

from tests.functional.utils import (
    EXPECTED_STATUSES,
    create_measure_starting_at_topic_page,
    navigate_to_topic_page,
    driver_login,
)

from tests.models import UserFactory, MeasureVersionFactory, DataSourceFactory

"""

THIS TEST MAKES SURE THAT MEASURES CAN BE REJECTED WHILE UNDER REVIEW

"""


def test_can_reject_a_measure_in_review_as_editor(driver, live_server, government_departments, frequencies_of_release):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
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

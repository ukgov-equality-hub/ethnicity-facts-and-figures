import random

from application.auth.models import TypeOfUser

from tests.functional.utils import create_measure_starting_at_topic_page, navigate_to_topic_page, driver_login
from tests.models import UserFactory, MeasureVersionFactory, DataSourceFactory


def test_secondary_source_can_be_added_and_removed(driver, live_server, government_departments, frequencies_of_release):
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

    # Add and save a secondary data source
    add_secondary_source = driver.find_element_by_link_text("Add secondary source")
    measure_edit_page.scroll_and_click(add_secondary_source)
    measure_edit_page.fill_secondary_data_source(sample_data_source)
    measure_edit_page.click_save()

    # Remove the secondary source
    remove_secondary_source = driver.find_element_by_link_text("Remove source")
    measure_edit_page.scroll_and_click(remove_secondary_source)
    measure_edit_page.click_save()

    # Check that you can re-add a secondary source
    add_secondary_source = driver.find_element_by_link_text("Add secondary source")
    assert add_secondary_source

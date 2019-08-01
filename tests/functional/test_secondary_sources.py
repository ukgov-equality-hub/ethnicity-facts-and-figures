import random

from application.auth.models import TypeOfUser

from tests.functional.pages import CreateDataSourcePage
from tests.functional.utils import (
    create_measure_starting_at_topic_page,
    navigate_to_topic_page,
    driver_login,
    fill_in,
    click_link_with_text,
    click_button_with_text,
)
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
    measure_edit_page.click_add_secondary_data_source()

    fill_in(driver, label_text="Search for an existing data source", with_text="My data source")

    click_button_with_text(driver, "Search")

    click_link_with_text(driver, "Create a new data source")

    data_source_page = CreateDataSourcePage(driver)
    data_source_page.fill_data_source(sample_data_source)
    data_source_page.click_save()
    data_source_page.click_back()

    # Remove the secondary source
    measure_edit_page.click_remove_secondary_data_source()

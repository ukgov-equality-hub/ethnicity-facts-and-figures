from application.auth.models import TypeOfUser
from tests.functional.pages import HomePage, TopicPage, MeasureEditPage
from tests.functional.utils import driver_login, fill_in, click_button_with_text, click_link_with_text
from tests.models import (
    UserFactory,
    TopicFactory,
    SubtopicFactory,
    DataSourceFactory,
    MeasureFactory,
    MeasureVersionFactory,
)


def test_adding_an_existing_data_source(driver, app, live_server):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)

    topic = TopicFactory.create(title="Police and crime")
    subtopic = SubtopicFactory.create(title="Policing", topic=topic)
    DataSourceFactory.create(title="Police statistics 2019")

    existing_measure = MeasureFactory.create(subtopics=[subtopic])
    MeasureVersionFactory.create(status="APPROVED", measure=existing_measure)

    driver_login(driver, live_server, rdu_user)
    home_page = HomePage(driver, live_server)

    home_page.click_topic_link(topic)

    topic_page = TopicPage(driver, live_server, topic)
    topic_page.expand_accordion_for_subtopic(subtopic)

    topic_page.click_add_measure(subtopic)

    create_measure_page = MeasureEditPage(driver)
    create_measure_page.set_title("Arrests")
    create_measure_page.click_save()

    create_measure_page.click_add_primary_data_source()

    fill_in(driver, label_text="Search for an existing data source", with_text="Police statistics")
    click_button_with_text(driver, "Search")

    label_for_existing_data_source = driver.find_element_by_xpath("//label[text()='Police statistics 2019']")

    label_for_existing_data_source.click()

    click_button_with_text(driver, "Select")

    assert "Successfully added the data source ‘Police statistics 2019’" in driver.page_source

    click_link_with_text(driver, "Preview this version")

    assert "Police statistics 2019" in driver.page_source

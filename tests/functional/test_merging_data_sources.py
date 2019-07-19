import pytest


from application.auth.models import TypeOfUser
from tests.functional.utils import driver_login
from tests.models import DataSourceFactory, UserFactory
from selenium.common.exceptions import NoSuchElementException


def test_merging_two_data_sources(driver, live_server):

    # Setup
    DataSourceFactory.create(title="Police statistics 2019")
    DataSourceFactory.create(title="Police stats 2019")
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER, active=True)

    driver_login(driver, live_server, admin_user)

    # When I go to the admin page
    driver.get(f"http://localhost:{live_server.port}/admin")

    # Then there should be a link to Data sources
    data_sources_link = driver.find_element_by_link_text("Data sources")
    assert data_sources_link

    # When I click the link
    data_sources_link.click()

    # Then I should be on the data sources page
    assert "Data sources" == driver.find_element_by_tag_name("h1").text

    assert "Select all options that represent the same data source" == driver.find_element_by_tag_name("legend").text

    data_source_1_label = driver.find_element_by_xpath("//label[text() = 'Police statistics 2019']")

    assert data_source_1_label

    data_source_2_label = driver.find_element_by_xpath("//label[text() = 'Police stats 2019']")

    assert data_source_2_label

    submit_button = driver.find_element_by_xpath("//button[text() = 'Continue']")

    assert submit_button

    # When I select the two data sources and click continue
    data_source_1_label.click()
    data_source_2_label.click()
    submit_button.click()

    # Then I should be on the merge data sources page

    assert "Merge 2 data sources" == driver.find_element_by_tag_name("h1").text
    assert "Which one would you like to keep?" == driver.find_element_by_tag_name("legend").text

    data_source_1_label = driver.find_element_by_xpath("//label[text() = 'Police statistics 2019']")

    assert data_source_1_label

    data_source_2_label = driver.find_element_by_xpath("//label[text() = 'Police stats 2019']")

    assert data_source_2_label

    submit_button = driver.find_element_by_xpath("//button[text() = 'Merge']")

    assert submit_button

    # When I select the first data source and click merge
    data_source_1_label.click()
    submit_button.click()

    # Then I should be back on the Data sources page
    assert "Data sources" == driver.find_element_by_tag_name("h1").text

    data_source_1_label = driver.find_element_by_xpath("//label[text() = 'Police statistics 2019']")

    assert data_source_1_label

    with pytest.raises(NoSuchElementException):
        data_source_2_label = driver.find_element_by_xpath("//label[text() = 'Police stats 2019']")

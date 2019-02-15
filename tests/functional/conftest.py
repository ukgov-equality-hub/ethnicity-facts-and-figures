import json
import os
import pytest

from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from application.cms.models import (
    Topic,
    MeasureVersion,
    Subtopic,
    FrequencyOfRelease,
    LowestLevelOfGeography,
    TypeOfStatistic,
    Organisation,
    DataSource,
    Measure,
)
from application.auth.models import User, TypeOfUser, CAPABILITIES


@pytest.fixture(scope="module")
def _driver():
    driver_name = os.getenv("SELENIUM_DRIVER", "chrome").lower()

    if driver_name == "firefox":
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", "Selenium")
        driver = webdriver.Firefox(profile, executable_path="/usr/local/bin/geckodriver")
        driver.set_window_position(0, 0)
        driver.set_window_size(1280, 720)

    elif driver_name == "chrome":
        d = DesiredCapabilities.CHROME
        d["loggingPrefs"] = {"browser": "ALL"}
        options = webdriver.ChromeOptions()
        options.add_argument("--kiosk")
        driver = webdriver.Chrome(
            options=options, desired_capabilities=d, executable_path="/usr/local/bin/chromedriver"
        )

    elif driver_name == "chrome_headless":
        # This is for CI, heroku chrome buildpack sets GOOGLE_CHROME_BIN itself
        # but we need to set CHROMEDRIVER_PATH ourselves so make sure env variable
        # for that is set correctly
        GOOGLE_CHROME_SHIM = os.environ["GOOGLE_CHROME_SHIM"]
        CHROMEDRIVER_PATH = os.environ["CHROMEDRIVER_PATH"]
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.binary_location = GOOGLE_CHROME_SHIM
        driver = webdriver.Chrome(options=options, executable_path=CHROMEDRIVER_PATH)

    elif driver_name == "phantomjs":
        driver = webdriver.PhantomJS()
        driver.maximize_window()

    else:
        raise ValueError("Invalid Selenium driver", driver_name)

    driver.delete_all_cookies()
    yield driver
    driver.delete_all_cookies()
    driver.close()


@pytest.fixture(scope="function")
def driver(_driver, request):
    prev_failed_tests = request.session.testsfailed
    yield _driver
    if prev_failed_tests != request.session.testsfailed:
        filename = str(Path.cwd() / "screenshots" / "{}_{}.png".format(datetime.utcnow(), request.function.__name__))
        _driver.save_screenshot(str(filename))
        print("Error screenshot saved to " + filename)


# TODO: Replace these with the main rdu_user and admin_user fixtures (or logged_in versions of them)
@pytest.fixture(scope="function")
def test_app_editor(db_session):
    user = User(email="editor@methods.co.uk", password="password123", active=True)
    user.user_type = TypeOfUser.RDU_USER
    user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def test_app_admin(db_session):
    user = User(email="admin@methods.co.uk", password="password123", active=True)
    user.user_type = TypeOfUser.ADMIN_USER
    user.capabilities = CAPABILITIES[TypeOfUser.ADMIN_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


# TODO: Delete these stubs after functional tests use FactoryBoy pages.
@pytest.fixture(scope="function")
def stub_compatible_topic(db_session):
    topic = Topic(id=98, slug="test", title="Test topic page", description="", additional_description="")
    db_session.session.add(topic)
    db_session.session.commit()
    return topic


@pytest.fixture(scope="function")
def stub_topic_page(db_session, stub_home_page, stub_compatible_topic):
    page = MeasureVersion(id=98, guid="topic_test", status="DRAFT", title="Test topic page", version="1.0")

    page.page_json = json.dumps({"guid": "topic_test", "title": "Test topic page"})

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_compatible_subtopic(db_session, stub_compatible_topic):
    subtopic = Subtopic(id=99, slug="example", title="Test subtopic page", topic_id=stub_compatible_topic.id)
    db_session.session.add(subtopic)
    db_session.session.commit()
    return subtopic


@pytest.fixture(scope="function")
def stub_subtopic_page(db_session, stub_topic_page, stub_compatible_subtopic):
    page = MeasureVersion(id=99, guid="subtopic_example", status="DRAFT", title="Test subtopic page", version="1.0")

    page.page_json = json.dumps({"guid": "subtopic_example", "title": "Test subtopic page"})

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_home_page(db_session):
    page = MeasureVersion(id=97, guid="homepage", status="DRAFT", title="Test homepage page", version="1.0")

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_frequency(db_session):
    frequency = FrequencyOfRelease(id=1, description="Quarterly", position=1)
    db_session.session.add(frequency)
    db_session.session.commit()
    return frequency


@pytest.fixture(scope="function")
def stub_geography(db_session):
    geography = LowestLevelOfGeography(name="UK", position=0)
    db_session.session.add(geography)
    db_session.session.commit()
    return geography


@pytest.fixture(scope="function")
def stub_type_of_statistic(db_session):
    type_of_statistic = TypeOfStatistic(id=1, internal="National", external="National", position=1)
    db_session.session.add(type_of_statistic)
    db_session.session.commit()
    return type_of_statistic


@pytest.fixture(scope="function")
def stub_organisations(db_session):
    organisation = Organisation(
        id="D10",
        name="Department for Work and Pensions",
        other_names=[],
        abbreviations=["DWP"],
        organisation_type="MINISTERIAL_DEPARTMENT",
    )
    db_session.session.add(organisation)
    db_session.session.commit()
    return organisation


@pytest.fixture(scope="function")
def stub_data_source(db_session, stub_organisations, stub_type_of_statistic, stub_frequency):
    data_source = DataSource(
        title="DWP Stats",
        type_of_data=["SURVEY"],
        type_of_statistic_id=stub_type_of_statistic.id,
        publisher_id=stub_organisations.id,
        source_url="http://dwp.gov.uk",
        publication_date="15th May 2017",
        note_on_corrections_or_updates="Note on corrections or updates",
        frequency_of_release_id=stub_frequency.id,
        purpose="Purpose of data source",
    )
    db_session.session.add(data_source)
    db_session.session.commit()

    return data_source


@pytest.fixture(scope="function")
def stub_compatible_measure(db_session, stub_compatible_subtopic):
    measure = Measure(slug="test-measure-page", position=0)
    measure.subtopics = [stub_compatible_subtopic]

    db_session.session.add(measure)
    db_session.session.commit()

    return measure


@pytest.fixture(scope="function")
def stub_measure_page(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_geography,
    stub_data_source,
    stub_compatible_measure,
):
    page = MeasureVersion(
        id=100,
        guid="test-measure-page",
        status="DRAFT",
        published=False,
        published_at=None,
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=True,
    )
    page.measure_id = (
        stub_compatible_measure.id
    )  # Duplicating page ID for simplicity during migration to new data model

    for key, val in stub_measure_data.items():
        setattr(page, key, val)

    page.data_sources = [stub_data_source]

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_published_measure_page(
    db_session, stub_subtopic_page, stub_measure_data, stub_frequency, stub_geography, stub_data_source
):  # TODO: Delete these stubs after using new hierarchy tables.
    page = MeasureVersion(
        id=_get_random_unused_measure_version_id(),
        guid="test-published-measure-page",
        status="APPROVED",
        published=True,
        published_at=datetime.now().date(),
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=True,
    )
    measure = Measure(id=page.id, slug="test-published-measure-page", reference=page.internal_reference)
    measure.subtopics = [Subtopic.query.get(stub_subtopic_page.id)]
    page.measure_id = page.id  # Duplicating page ID for simplicity during migration to new data model

    for key, val in stub_measure_data.items():
        setattr(page, key, val)

    page.data_sources = [stub_data_source]

    db_session.session.add(measure)
    db_session.session.add(page)
    db_session.session.commit()
    return page


def _get_random_unused_measure_version_id():
    from random import randint

    id = randint(1, 99999)
    while MeasureVersion.query.filter_by(id=id).first() is not None:
        id = randint(1, 99999)
    return id


# TODO: END REMOVE THESE STUBS

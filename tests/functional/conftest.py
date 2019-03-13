import os
import pytest

from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from tests.models import OrganisationFactory, FrequencyOfReleaseFactory


@pytest.fixture(scope="module")
def _driver():
    driver_name = os.getenv("SELENIUM_DRIVER", "chrome").lower()

    if driver_name == "firefox":
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", "Selenium")
        driver = webdriver.Firefox(profile, executable_path="/usr/local/bin/geckodriver")
        driver.set_window_position(0, 0)
        driver.set_window_size(1920, 1080)

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
        driver.set_window_size(1920, 1080)

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


@pytest.fixture(scope="function")
def frequencies_of_release(_configure_factory_sessions):
    frequencies = [
        FrequencyOfReleaseFactory(description="Monthly"),
        FrequencyOfReleaseFactory(description="Quarterly"),
        FrequencyOfReleaseFactory(description="3 times a year"),
        FrequencyOfReleaseFactory(description="Twice a year"),
        FrequencyOfReleaseFactory(description="Yearly"),
        FrequencyOfReleaseFactory(description="Every 2 years"),
        FrequencyOfReleaseFactory(description="Every 3 years"),
        FrequencyOfReleaseFactory(description="Every 4 years"),
        FrequencyOfReleaseFactory(description="Every 5 years"),
        FrequencyOfReleaseFactory(description="Ad-hoc"),
        FrequencyOfReleaseFactory(description="Other"),
    ]

    return frequencies


@pytest.fixture(scope="function")
def government_departments(_configure_factory_sessions):
    organisations = [
        OrganisationFactory(name="Race Disparity Unit", other_names=[], abbreviations=["RDU"]),
        OrganisationFactory(name="Ministry of Justice", other_names=[], abbreviations=["MoJ", "MOJ"]),
        OrganisationFactory(name="Crown Prosecution Service", other_names=[], abbreviations=["CPS"]),
        OrganisationFactory(
            name="Department for Work and Pensions",
            other_names=["Department for Work & Pensions"],
            abbreviations=["DWP"],
        ),
    ]

    return organisations

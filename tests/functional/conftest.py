import os
import pytest

from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


@pytest.fixture(scope="module")
def _driver():
    driver_name = os.getenv('SELENIUM_DRIVER', 'chrome_headless').lower()

    if driver_name == 'firefox':
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", "Selenium")
        driver = webdriver.Firefox(profile, executable_path="/usr/local/bin/geckodriver")
        driver.set_window_position(0, 0)
        driver.set_window_size(1280, 720)

    elif driver_name == 'chrome':
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = {'browser': 'ALL'}
        options = webdriver.ChromeOptions()
        options.add_argument("--kiosk")
        driver = webdriver.Chrome(chrome_options=options,
                                  desired_capabilities=d,
                                  executable_path='/usr/local/bin/chromedriver')

    elif driver_name == 'chrome_headless':
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options=options, executable_path='/usr/local/bin/chromedriver')

    elif driver_name == 'phantomjs':
        driver = webdriver.PhantomJS()
        driver.maximize_window()

    else:
        raise ValueError('Invalid Selenium driver', driver_name)

    driver.delete_all_cookies()
    yield driver
    driver.delete_all_cookies()
    driver.close()


@pytest.fixture(scope='function')
def driver(_driver, request):
    prev_failed_tests = request.session.testsfailed
    yield _driver
    if prev_failed_tests != request.session.testsfailed:
        filename = str(Path.cwd() / 'screenshots' / '{}_{}.png'.format(datetime.utcnow(), request.function.__name__))
        _driver.save_screenshot(str(filename))
        print('Error screenshot saved to ' + filename)

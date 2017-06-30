from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.functional.elements import UsernameInputElement, PasswordInputElement
from tests.functional.locators import NavigationLocators, LoginPageLocators, FooterLinkLocators


class RetryException(Exception):
    pass


class BasePage:

    log_out_link = NavigationLocators.LOG_OUT_LINK

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url

    def wait_for_invisible_element(self, locator):
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_element(self, locator):
        return WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(locator),
            EC.presence_of_element_located(locator)
        )

    def log_out(self):
        element = self.wait_for_element(BasePage.log_out_link)
        element.click()
        self.driver.delete_all_cookies()

    def wait_until_url_is(self, url):
        return WebDriverWait(self.driver, 10).until(
            self.url_contains(url)
        )

    def url_contains(self, url):
        def check_contains_url(driver):
            return url in self.driver.current_url
        return check_contains_url

    def select_checkbox_or_radio(self, element):
        self.driver.execute_script("arguments[0].setAttribute('checked', 'checked')", element)


class LogInPage(BasePage):

    login_button = LoginPageLocators.LOGIN_BUTTON
    username_input = UsernameInputElement()
    password_input = PasswordInputElement()

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s' % live_server.port)

    def get(self):
        url = '%s/auth/login' % self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is('%s/auth/login' % self.base_url)

    def fill_login_form(self, username, password):
        self.username_input = username
        self.password_input = password

    def click_login_button(self):
        element = self.wait_for_element(LogInPage.login_button)
        element.click()

    def login(self, username, password):
        self.fill_login_form(username, password)
        self.click_login_button()


class IndexPage(BasePage):

    cms_link = FooterLinkLocators.CMS_LINK

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s' % live_server.port)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_cms_link(self):
        element = self.wait_for_element(IndexPage.cms_link)
        element.click()


class CmsIndexPage(BasePage):

    # cms_link = FooterLinkLocators.CMS_LINK

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms' % live_server.port)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    # def click_cms_link(self):
    #     element = self.wait_for_element(IndexPage.cms_link)
    #     element.click()

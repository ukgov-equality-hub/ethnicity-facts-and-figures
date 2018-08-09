from selenium.webdriver.support.ui import WebDriverWait

from tests.functional.locators import LoginPageLocators


class BasePageElement:
    def __set__(self, obj, value):
        driver = obj.driver
        WebDriverWait(driver, 100).until(lambda driver: driver.find_element_by_name(self.locator))
        driver.find_element_by_name(self.locator).send_keys(value)

    def __get__(self, obj, owner):
        driver = obj.driver
        WebDriverWait(driver, 100).until(lambda driver: driver.find_element_by_name(self.locator))
        element = driver.find_element_by_name(self.locator)
        return element.get_attribute("value")


class UsernameInputElement(BasePageElement):
    locator = LoginPageLocators.USER_NAME_INPUT[1]


class PasswordInputElement(BasePageElement):
    locator = LoginPageLocators.PASSWORD_INPUT[1]


class LoginButtonElement(BasePageElement):
    locator = LoginPageLocators.LOGIN_BUTTON[1]

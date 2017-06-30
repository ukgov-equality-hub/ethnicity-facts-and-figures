from selenium.webdriver.common.by import By


class LoginPageLocators:
    USER_NAME_INPUT = (By.NAME, 'email')
    PASSWORD_INPUT = (By.NAME, 'password')
    H1 = (By.TAG_NAME, 'H1')
    LOGIN_BUTTON = (By.NAME, 'login')


class NavigationLocators:
    LOG_OUT_LINK = (By.LINK_TEXT, 'Log out')


class FooterLinkLocators:
    CMS_LINK = (By.LINK_TEXT, 'CMS')

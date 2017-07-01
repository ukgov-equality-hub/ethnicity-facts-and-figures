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


class PageLinkLocators:
    HOME_BREADCRUMB = (By.ID, 'home_breadcrumb')
    NEW_MEASURE = (By.LINK_TEXT, 'Add a measure')

    @staticmethod
    def page_link(page):
        return By.LINK_TEXT, page.title

    @staticmethod
    def breadcrumb_link(page):
        return By.ID, '%s_breadcrumb' % page.guid

class CreateMeasureLocators:
    GUID_INPUT = (By.NAME, 'guid')
    TITLE_INPUT = (By.NAME, 'title')
    SAVE_BUTTON = (By.NAME, 'save')


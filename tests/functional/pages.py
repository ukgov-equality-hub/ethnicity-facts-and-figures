from faker import Faker
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.functional.elements import UsernameInputElement, PasswordInputElement
from tests.functional.locators import NavigationLocators, LoginPageLocators, FooterLinkLocators, PageLinkLocators, \
    CreateMeasureLocators, EditMeasureLocators, DimensionPageLocators


class RetryException(Exception):
    pass


class BasePage:

    log_out_link = NavigationLocators.LOG_OUT_LINK

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

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

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms' % live_server.port)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_topic_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        element.click()


class TopicPage(BasePage):

    def __init__(self, driver, live_server, page):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms/%s' % (live_server.port, page.guid))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_subtopic_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        element.click()

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        element.click()


class SubtopicPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms/%s/%s'
                                                 % (live_server.port, topic_page.guid, subtopic_page.guid))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_measure_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        element.click()

    def click_preview_measure_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        element.click()

    def click_breadcrumb_for_page(self, page):
        element = self.wait_for_element(PageLinkLocators.breadcrumb_link(page))
        element.click()

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        element.click()

    def click_new_measure(self):
        element = self.wait_for_element(PageLinkLocators.NEW_MEASURE)
        element.click()


class MeasureCreatePage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms/%s/%s/measure/new'
                                                 % (live_server.port, topic_page.guid, subtopic_page.guid))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def set_guid(self, guid):
        element = self.wait_for_element(CreateMeasureLocators.GUID_INPUT)
        element.clear()
        element.send_keys(guid)

    def set_title(self, title):
        element = self.wait_for_element(CreateMeasureLocators.TITLE_INPUT)
        element.clear()
        element.send_keys(title)

    def click_save(self):
        element = self.wait_for_element(CreateMeasureLocators.SAVE_BUTTON)
        element.click()


class MeasureVersionsPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page, measure_page_guid):
        super().__init__(driver=driver,
                         base_url='http://localhost:%s/cms/%s/%s/%s/versions'
                                  % (live_server.port,
                                     topic_page.guid,
                                     subtopic_page.guid,
                                     measure_page_guid,))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def click_measure_version_link(self, page):
        link_text = 'Version %s - %s' % (page.version, page.created_at.strftime('%d %B %Y'))
        element = self.wait_for_element(PageLinkLocators.page_link(link_text))
        element.click()


class MeasureEditPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page, measure_page_guid, measure_page_version):
        super().__init__(driver=driver,
                         base_url='http://localhost:%s/cms/%s/%s/%s/%s/edit'
                                  % (live_server.port,
                                     topic_page.guid,
                                     subtopic_page.guid,
                                     measure_page_guid,
                                     measure_page_version))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_breadcrumb_for_page(self, page):
        element = self.wait_for_element(PageLinkLocators.breadcrumb_link(page))
        element.click()

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        element.click()

    def click_save(self):
        element = self.wait_for_element(EditMeasureLocators.SAVE_BUTTON)
        element.click()

    def click_add_dimension(self):
        element = self.wait_for_element(EditMeasureLocators.ADD_DIMENSION_LINK)
        self.driver.execute_script("return arguments[0].scrollIntoView();", element)
        element.click()

    def click_preview(self):
        element = self.wait_for_element(EditMeasureLocators.PREVIEW_LINK)
        element.click()

    def set_title(self, title):
        element = self.wait_for_element(EditMeasureLocators.TITLE_INPUT)
        element.clear()
        element.send_keys(title)

    def set_publication_date(self, date):
        element = self.wait_for_element(EditMeasureLocators.PUBLICATION_DATE_PICKER)
        # element.clear()
        element.send_keys(date)

    def set_measure_summary(self, measure_summary):
        element = self.wait_for_element(EditMeasureLocators.MEASURE_SUMMARY_TEXTAREA)
        element.clear()
        element.send_keys(measure_summary)

    def set_main_points(self, main_points):
        element = self.wait_for_element(EditMeasureLocators.MAIN_POINTS_TEXTAREA)
        element.clear()
        element.send_keys(main_points)


class DimensionAddPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page, measure_page):
        super().__init__(driver=driver,
                         base_url='http://localhost:%s/cms/%s/%s/%s/%s/dimension/new'
                                  % (live_server.port,
                                     topic_page.guid,
                                     subtopic_page.guid,
                                     measure_page.guid,
                                     measure_page.version))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def set_title(self, title):
        element = self.wait_for_element(DimensionPageLocators.TITLE_INPUT)
        element.clear()
        element.send_keys(title)

    def set_time_period(self, time_period):
        element = self.wait_for_element(DimensionPageLocators.TIME_PERIOD_INPUT)
        element.clear()
        element.send_keys(time_period)

    def set_summary(self, summary):
        element = self.wait_for_element(DimensionPageLocators.SUMMARY_TEXTAREA)
        element.clear()
        element.send_keys(summary)

    def click_save(self):
        element = self.wait_for_element(DimensionPageLocators.SAVE_BUTTON)
        element.click()


class DimensionEditPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.source_contains('Edit dimension')

    def source_contains(self, text):
        return text in self.driver.page_source

    def set_suppression_rules(self, suppression_rules):
        element = self.wait_for_element(DimensionPageLocators.SUPPRESSION_RULES_TEXTAREA)
        element.clear()
        element.send_keys(suppression_rules)

    def set_disclosure_control(self, disclosure_control):
        element = self.wait_for_element(DimensionPageLocators.DISCLOSURE_CONTROL_TEXTAREA)
        element.clear()
        element.send_keys(disclosure_control)

    def click_update(self):
        element = self.wait_for_element(DimensionPageLocators.UPDATE_BUTTON)
        element.click()


class MeasurePreviewPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page, measure_page):
        super().__init__(driver=driver,
                         base_url='http://localhost:%s/%s/%s/%s/%s'
                                  % (live_server.port,
                                     topic_page.uri,
                                     subtopic_page.uri,
                                     measure_page.uri,
                                     measure_page.version))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def source_contains(self, text):
        return text in self.driver.page_source


class RandomMeasure:

    def __init__(self):
        factory = Faker()
        self.guid = '%s_%s' % (factory.word(), factory.random_int(1, 1000))
        self.version = '1.0'
        self.publication_date = factory.date('%d%m%Y')
        self.published = False
        self.title = ' '.join(factory.words(4))
        self.measure_summary = factory.text()
        self.main_points = factory.text()
        self.geographic_coverage = factory.text(100)
        self.lowest_level_of_geography = factory.text(100)
        self.time_covered = factory.text(100)
        self.need_to_know = factory.text()
        self.ethnicity_definition_detail = factory.text()
        self.ethnicity_definition_summary = factory.text()
        self.source_text = factory.text(100)
        self.source_url = factory.url()
        self.department_source = factory.text(100)
        self.published_date = factory.date()
        self.last_update = factory.date()
        self.next_update = factory.date()
        self.frequency = factory.word()
        self.related_publications = factory.text()
        self.contact_phone = factory.phone_number()
        self.contact_email = factory.company_email()
        self.data_source_purpose = factory.text()
        self.methodology = factory.text()
        self.data_type = factory.word()
        self.suppression_rules = factory.text()
        self.disclosure_controls = factory.text()
        self.estimation = factory.word()
        self.type_of_statistic = factory.word()
        self.qui_url = factory.url()
        self.further_technical_information = factory.text()


class RandomDimension():
    def __init__(self):
        factory = Faker()
        self.title = ' '.join(factory.words(4))
        self.time_period = ' '.join(factory.words(4))
        self.summary = factory.text(100)
        self.suppression_rules = factory.text(100)
        self.disclosure_control = factory.text(100)
        self.type_of_statistic = ' '.join(factory.words(4))
        self.location = ' '.join(factory.words(4))
        self.source = ' '.join(factory.words(4))

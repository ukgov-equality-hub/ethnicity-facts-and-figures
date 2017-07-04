from selenium.webdriver.common.by import By
from faker import Faker


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


class EditMeasureLocators:
    SAVE_BUTTON = (By.NAME, 'save')
    PREVIEW_LINK = (By.NAME, 'preview')
    ADD_DIMENSION_LINK = (By.LINK_TEXT, 'Add dimension')

    PUBLICATION_DATE_PICKER = (By.NAME, 'publication_date')
    PUBLISHED_LABEL = (By.NAME, 'published')
    TITLE_INPUT = (By.NAME, 'title')
    MEASURE_SUMMARY_TEXTAREA = (By.NAME, 'measure_summary')
    MAIN_POINTS_TEXTAREA = (By.NAME, 'summary')
    GEOGRAPHIC_COVERAGE_TEXTAREA = (By.NAME, 'geographic_coverage')
    LOWEST_LEVEL_OF_GEOGRAPHY_TEXTAREA = (By.NAME, 'lowest_level_of_geography')
    TIME_COVERED_TEXTAREA = (By.NAME, 'time_covered')
    NEED_TO_KNOW_TEXTAREA = (By.NAME, 'need_to_know')
    ETHNICITY_DEFINITION_DETAIL_TEXTAREA = (By.NAME, 'ethnicity_definition_detail')
    ETHNICITY_SUMMARY_DETAIL_TEXTAREA = (By.NAME, 'ethnicity_definition_summary')
    SOURCE_TEXT_TEXTAREA = (By.NAME, 'source_text')
    SOURCE_URL_INPUT = (By.NAME, 'source_url')
    DEPARTMENT_SOURCE_TEXTAREA = (By.NAME, 'department_source')
    PUBLISHED_DATE_INPUT = (By.NAME, 'published_date')
    LAST_UPDATE_INPUT = (By.NAME, 'last_update_date')
    NEXT_UPDATE_INPUT = (By.NAME, 'next_update_date')
    FREQUENCY_INPUT = (By.NAME, 'frequency')
    RELATED_PUBLICATIONS_TEXTAREA = (By.NAME, 'related_publications')
    CONTACT_PHONE_INPUT = (By.NAME, 'contact_phone')
    CONTACT_EMAIL_INPUT = (By.NAME, 'contact_email')
    DATA_SOURCE_PURPOSE_TEXTAREA = (By.NAME, 'data_source_purpose')
    METHODOLOGY_TEXTAREA = (By.NAME, 'methodology')
    DATA_TYPE_INPUT = (By.NAME, 'data_type')
    SUPPRESSION_RULES_TEXTAREA = (By.NAME, 'suppression_rules')
    DISCLOSURE_CONTROLS_TEXTAREA = (By.NAME, 'disclosure_controls')
    ESTIMATION_TEXTAREA = (By.NAME, 'estimation')
    TYPE_OF_STATISTIC_INPUT = (By.NAME, 'type_of_statistic')
    QMI_URL_INPUT = (By.NAME, 'qmi_url')
    FURTHER_TECHNICAL_INFORMATION_INPUT = (By.NAME, 'further_technical_information')


class DimensionPageLocators:
    TITLE_INPUT = (By.NAME, 'title')
    TIME_PERIOD_INPUT = (By.NAME, 'time_period')
    SUMMARY_TEXTAREA = (By.NAME, 'summary')
    SUPPRESSION_RULES_TEXTAREA = (By.NAME, 'suppression_rules')
    DISCLOSURE_CONTROL_TEXTAREA = (By.NAME, 'disclosure_control')
    TYPE_OF_STATISTIC_INPUT = (By.NAME, 'type_of_statistic')
    LOCATION_INPUT = (By.NAME, 'location')
    SOURCE_INPUT = (By.NAME, 'source')
    SAVE_BUTTON = (By.NAME, 'save')
    UPDATE_BUTTON = (By.NAME, 'update')

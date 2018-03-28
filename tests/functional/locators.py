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
    HOME_BREADCRUMB = (By.LINK_TEXT, 'Ethnicity facts and figures')
    NEW_MEASURE = (By.LINK_TEXT, 'Add a measure')

    @staticmethod
    def page_link(link_text):
        return By.LINK_TEXT, link_text

    @staticmethod
    def breadcrumb_link(page):
        return By.LINK_TEXT, page.title


class CreateMeasureLocators:
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
    CREATE_CHART = (By.ID, 'create_chart')
    CREATE_TABLE = (By.ID, 'create_table')


class ChartBuilderPageLocators:
    DATA_TEXT_AREA = (By.ID, 'data_text_area')
    CHART_TYPE_SELECTOR = (By.ID, 'chart_type_selector')
    BAR_CHART_PRIMARY = (By.ID, 'primary_column')
    BAR_CHART_SECONDARY = (By.ID, 'secondary_column')
    BAR_CHART_ORDER = (By.ID, 'order_column')
    OPTIONS_CHART_TITLE = (By.ID, 'chart_title')
    OPTIONS_X_AXIS = (By.ID, 'x_axis_label')
    OPTIONS_Y_AXIS = (By.ID, 'y_axis_label')
    OPTIONS_NUMBER_FORMAT = (By.ID, 'number_format')
    CHART_PREVIEW = (By.ID, 'preview')
    CHART_SAVE = (By.ID, 'save')
    CHART_BACK = (By.ID, 'exit')
    PANEL_BAR_CHART_PRIMARY = (By.ID, 'panel_primary_column')
    PANEL_BAR_CHART_SECONDARY = (By.ID, 'panel_grouping_column')


class TableBuilderPageLocators:
    DATA_TEXT_AREA = (By.ID, 'data_text_area')
    TABLE_TITLE_BOX = (By.ID, 'table_title')
    ROWS_SELECTOR = (By.ID, 'table_category_column')
    GROUPING_SELECTOR = (By.ID, 'table_group_column')
    TABLE_PREVIEW = (By.ID, 'preview')
    TABLE_SAVE = (By.ID, 'save')
    COLUMN_SELECTOR_1 = (By.ID, 'table_column_1')
    COLUMN_SELECTOR_2 = (By.ID, 'table_column_2')
    COLUMN_SELECTOR_3 = (By.ID, 'table_column_3')
    COLUMN_SELECTOR_4 = (By.ID, 'table_column_4')
    COLUMN_SELECTOR_5 = (By.ID, 'table_column_5')


class TopicPageLocators:

    @staticmethod
    def get_accordion(data_event_text):
        return By.CSS_SELECTOR, "div[data-event-label='%s']" % data_event_text

    @staticmethod
    def get_add_measure_link(link_text):
        return By.LINK_TEXT, "Add a measure to %s" % link_text

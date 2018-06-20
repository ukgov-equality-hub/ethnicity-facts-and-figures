from selenium.webdriver.common.by import By


class LoginPageLocators:
    USER_NAME_INPUT = (By.NAME, 'email')
    PASSWORD_INPUT = (By.NAME, 'password')
    H1 = (By.TAG_NAME, 'H1')
    LOGIN_BUTTON = (By.NAME, 'login')


class NavigationLocators:
    LOG_OUT_LINK = (By.LINK_TEXT, 'Sign out')


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


class MeasureActionLocators:
    @staticmethod
    def view_link(measure):
        print('measure_action__view-%s' % measure.guid)
        return By.ID, 'measure_action__view-%s' % measure.guid

    @staticmethod
    def delete_link(measure):
        return By.ID, 'measure_action__delete-%s' % measure.guid


class CreateMeasureLocators:
    TITLE_INPUT = (By.NAME, 'title')
    SAVE_BUTTON = (By.NAME, 'save')


class EditMeasureLocators:

    @staticmethod
    def lowest_level_of_geography_radio_button(index_value):
        # index_value should be in the range 0 to 6
        return (By.ID, 'lowest_level_of_geography_id-%s' % str(index_value))

    @staticmethod
    def frequency_radio_button(index_value):
        # index_value should be in the range 0 to 6
        return (By.ID, 'frequency_id-%s' % str(index_value))

    @staticmethod
    def type_of_statistic_radio_button(index_value):
        # index_value should be in the range 0 to 6
        return (By.ID, 'type_of_statistic_id-%s' % str(index_value))

    STATUS_LABEL = (By.ID, 'status')
    LOWEST_LEVEL_OF_GEOGRAPHY_RADIO = (By.XPATH, "//*[@type='radio']")
    SAVE_BUTTON = (By.NAME, 'save')
    SAVE_AND_REVIEW_BUTTON = (By.NAME, 'save-and-review')
    SEND_TO_DEPARTMENT_REVIEW_BUTTON = (By.ID, 'send-to-department-review')
    SEND_TO_APPROVED = (By.ID, 'send-to-approved')
    DEPARTMENT_REVIEW_LINK = (By.ID, 'review-link-url')

    PREVIEW_LINK = (By.NAME, 'preview')
    ADD_DIMENSION_LINK = (By.LINK_TEXT, 'Add dimension')

    PUBLICATION_DATE_PICKER = (By.NAME, 'publication_date')
    PUBLISHED_LABEL = (By.NAME, 'published')
    TITLE_INPUT = (By.NAME, 'title')
    MEASURE_SUMMARY_TEXTAREA = (By.NAME, 'measure_summary')
    SUMMARY_TEXTAREA = (By.NAME, 'summary')
    GEOGRAPHIC_COVERAGE_TEXTAREA = (By.NAME, 'geographic_coverage')
    LOWEST_LEVEL_OF_GEOGRAPHY_TEXTAREA = (By.NAME, 'lowest_level_of_geography')
    TIME_COVERED_TEXTAREA = (By.NAME, 'time_covered')
    NEED_TO_KNOW_TEXTAREA = (By.NAME, 'need_to_know')
    ETHNICITY_DEFINITION_DETAIL_TEXTAREA = (By.NAME, 'ethnicity_definition_detail')
    ETHNICITY_SUMMARY_DETAIL_TEXTAREA = (By.NAME, 'ethnicity_definition_summary')
    SOURCE_TEXT_TEXTAREA = (By.NAME, 'source_text')
    SOURCE_URL_INPUT = (By.NAME, 'source_url')
    DEPARTMENT_SOURCE_TEXTAREA = (By.ID, 'department-source')
    PUBLISHED_DATE_INPUT = (By.NAME, 'published_date')
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
    CHART_DATA_OKAY = (By.ID, 'confirm-data')
    CHART_DATA_CANCEL = (By.ID, 'cancel-edit-data')
    PANEL_BAR_CHART_PRIMARY = (By.ID, 'panel_primary_column')
    PANEL_BAR_CHART_SECONDARY = (By.ID, 'panel_grouping_column')
    CHART_ETHNICITY_SETTINGS = (By.ID, 'ethnicity_settings')

    CHART_LINE_X_AXIS = (By.ID, 'line__x-axis_column')

    CHART_GROUPED_BAR_DATA_STYLE = (By.ID, 'grouped-bar__data_style')
    CHART_GROUPED_BAR_COLUMN = (By.ID, 'grouped-bar__bar_column')
    CHART_GROUPED_GROUPS_COLUMN = (By.ID, 'grouped-bar__groups_column')

    CHART_COMPONENT_DATA_STYLE = (By.ID, 'component__data_style')
    CHART_COMPONENT_SECTION_COLUMN = (By.ID, 'component__section_column')
    CHART_COMPONENT_BAR_COLUMN = (By.ID, 'component__bar_column')

    CHART_PANEL_DATA_STYLE = (By.ID, 'panel-bar__data_style')
    CHART_PANEL_BAR_COLUMN = (By.ID, 'panel-bar__bar_column')
    CHART_PANEL_PANEL_COLUMN = (By.ID, 'panel-bar__panel_column')

    CHART_PANEL_X_AXIS_COLUMN = (By.ID, 'panel-line__x-axis_column')


class TableBuilderPageLocators:
    DATA_TEXT_AREA = (By.ID, 'data_text_area')
    TABLE_TITLE_BOX = (By.ID, 'table_title')
    ROWS_SELECTOR = (By.ID, 'table_category_column')
    GROUPING_SELECTOR = (By.ID, 'table_group_column')
    TABLE_PREVIEW = (By.ID, 'preview')
    TABLE_SAVE = (By.ID, 'save')
    TABLE = (By.ID, 'container')
    TABLE_ERROR_CONTAINER = (By.ID, 'error_container')
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

    @staticmethod
    def get_measure_link(measure):
        return By.LINK_TEXT, measure.title

    @staticmethod
    def get_measure_edit_link(measure):
        return By.ID, 'measure-action-section__edit_button-%s' % measure.guid

    @staticmethod
    def get_measure_view_form_link(measure):
        return By.ID, 'measure-action-section__view_form_link-%s' % measure.guid

    @staticmethod
    def get_measure_create_new_link(measure):
        return By.ID, 'measure-action-section__create_new_link-%s' % measure.guid

    @staticmethod
    def get_measure_delete_link(measure):
        return By.ID, 'measure-action-section__delete_button-%s' % measure.guid

    @staticmethod
    def get_measure_confirm_yes_radio(measure):
        return By.ID, 'delete-radio-yes-%s' % measure.guid

    @staticmethod
    def get_measure_confirm_no_radio(measure):
        return By.ID, 'delete-radio-yes-%s' % measure.guid

    @staticmethod
    def get_measure_confirm_delete_button(measure):
        return By.ID, 'delete-confirm-button-%s' % measure.guid

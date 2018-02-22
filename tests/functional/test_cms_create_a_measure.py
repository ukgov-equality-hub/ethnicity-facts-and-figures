import pytest

from application.cms.page_service import PageService
from tests.functional.locators import ChartBuilderPageLocators
from tests.functional.pages import LogInPage, HomePage, CmsIndexPage, TopicPage, SubtopicPage, MeasureEditPage, \
    MeasureCreatePage, RandomMeasure, MeasurePreviewPage, RandomDimension, DimensionAddPage, DimensionEditPage, \
    ChartBuilderPage, TableBuilderPage

import time

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_can_create_a_measure_page(driver,
                                   app,
                                   test_app_editor,
                                   live_server,
                                   stub_topic_page,
                                   stub_subtopic_page):
    page = RandomMeasure()

    login(driver, live_server, test_app_editor)

    home_page = HomePage(driver, live_server)
    home_page.click_topic_link(stub_topic_page)

    topic_page = TopicPage(driver, live_server, stub_topic_page)
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)
    topic_page.click_add_measure(stub_subtopic_page)

    create_measure(driver, live_server, page, stub_topic_page, stub_subtopic_page)

    edit_measure_page = MeasureEditPage(driver,
                                        live_server,
                                        stub_topic_page,
                                        stub_subtopic_page,
                                        page.guid,
                                        page.version)

    assert edit_measure_page.is_current()

    '''
    EDIT A MEASURE
    Save some information to the edit page
    '''
    edit_measure_page.set_measure_summary(page.measure_summary)
    edit_measure_page.set_main_points(page.main_points)
    edit_measure_page.click_save()
    assert edit_measure_page.is_current()

    '''
    PREVIEW PAGE
    Go to preview page
    '''
    edit_measure_page.click_preview()

    page_service = PageService()
    page_service.init_app(app)
    measure_page = page_service.get_page(page.guid)

    preview_measure_page = MeasurePreviewPage(driver, live_server, stub_topic_page, stub_subtopic_page, measure_page)
    assert preview_measure_page.is_current()

    assert_page_contains(preview_measure_page, page.title)
    assert_page_contains(preview_measure_page, page.measure_summary)
    assert_page_contains(preview_measure_page, page.main_points)

    '''
    ADD A DIMENSION
    Save some dimension data
    '''
    edit_measure_page.get()
    assert edit_measure_page.is_current()

    dimension = RandomDimension()
    edit_measure_page.click_add_dimension()

    create_dimension_page = DimensionAddPage(driver, live_server, stub_topic_page, stub_subtopic_page, measure_page)
    create_dimension_page.get()

    create_dimension_page.set_title(dimension.title)
    create_dimension_page.set_time_period(dimension.time_period)
    create_dimension_page.set_summary(dimension.summary)
    create_dimension_page.click_save()

    edit_dimension_page = DimensionEditPage(driver)
    assert edit_dimension_page.is_current()

    preview_measure_page.get()
    assert_page_contains(preview_measure_page, dimension.title)
    assert_page_contains(preview_measure_page, dimension.time_period)
    assert_page_contains(preview_measure_page, dimension.summary)

    '''
    EDIT A DIMENSION
    '''
    edit_dimension_page.get()
    assert edit_dimension_page.is_current()

    edit_dimension_page.set_summary('some updated text')
    edit_dimension_page.click_update()

    assert edit_dimension_page.is_current()

    preview_measure_page.get()
    assert_page_contains(preview_measure_page, 'some updated text')

    '''
    CREATE A SIMPLE CHART
    '''
    edit_dimension_page.get()
    assert edit_dimension_page.is_current()

    edit_dimension_page.click_create_chart()
    edit_dimension_page.wait_until_url_contains('create_chart')

    chart_builder_page = ChartBuilderPage(driver, edit_dimension_page)
    assert chart_builder_page.is_current()

    chart_builder_page.paste_data(data=[['Ethnicity', 'Value'], ['White', '1'], ['BAME', '2']])
    chart_builder_page.wait_for_seconds(2)
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(2)

    chart_builder_page.wait_until_select_contains(ChartBuilderPageLocators.BAR_CHART_PRIMARY, 'Ethnicity')
    chart_builder_page.select_bar_chart_category('Ethnicity')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.click_preview()
    chart_builder_page.wait_for_seconds(2)

    chart_builder_page.get()
    chart_builder_page.paste_data(data=[['Ethnicity', 'Gender', 'Value'],
                                        ['a', 'c', '5'], ['b', 'c', '7'],
                                        ['a', 'd', '6'], ['b', 'd', '9']])
    chart_builder_page.wait_for_seconds(2)
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.wait_until_select_contains(ChartBuilderPageLocators.BAR_CHART_PRIMARY, 'Ethnicity')
    chart_builder_page.select_bar_chart_category('Ethnicity')

    chart_builder_page.wait_until_select_contains(ChartBuilderPageLocators.BAR_CHART_SECONDARY, 'Gender')
    chart_builder_page.select_bar_chart_group('Gender')

    chart_builder_page.click_preview()

    chart_builder_page.wait_for_seconds(3)

    chart_builder_page.select_chart_type('Panel bar chart')

    chart_builder_page.wait_until_select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_PRIMARY, 'Ethnicity')
    chart_builder_page.select_panel_bar_chart_primary('Ethnicity')
    chart_builder_page.wait_until_select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_SECONDARY, 'Gender')
    chart_builder_page.select_panel_bar_chart_grouping('Gender')
    chart_builder_page.click_preview()

    chart_builder_page.click_save()
    chart_builder_page.wait_for_seconds(3)

    chart_builder_page.click_back()

    '''
    CREATE A SIMPLE TABLE
    '''
    assert edit_dimension_page.is_current()
    edit_dimension_page.click_create_table()

    table_builder_page = TableBuilderPage(driver)
    assert table_builder_page.is_current()

    table_builder_page.paste_data(data=[['Ethnicity', 'Value'], ['a', '1'], ['b', '2']])
    table_builder_page.wait_for_seconds(2)
    table_builder_page.select_category('Ethnicity')
    table_builder_page.select_column_1('Value')
    table_builder_page.click_preview()
    table_builder_page.wait_for_seconds(2)

    '''
    CREATE A TABLE WITH TWO COLUMNS
    '''
    table_builder_page.get()
    table_builder_page.paste_data(data=[['Ethnicity', 'Gender', 'Count'],
                                        ['White', 'Male', '1'], ['BAME', 'Male', '3'],
                                        ['White', 'Female', '2'], ['BAME', 'Female', '4']])
    table_builder_page.wait_for_seconds(1)

    table_builder_page.select_category('Ethnicity')
    table_builder_page.wait_for_seconds(1)
    table_builder_page.select_grouping('Gender')
    table_builder_page.wait_for_seconds(1)
    table_builder_page.select_column_1('Count')

    table_builder_page.click_preview()
    table_builder_page.wait_for_seconds(2)

    table_builder_page.click_save()


def go_to_page(page):
    page.get()
    assert page.is_current()
    return page


def assert_page_contains(page, text):
    return page.source_contains(text)


def create_measure(driver, live_server, page, topic, subtopic):
    create_measure_page = MeasureCreatePage(driver, live_server, topic, subtopic)
    create_measure_page.set_title(page.title)
    create_measure_page.click_save()


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

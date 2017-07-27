import pytest

from application.cms.page_service import PageService
from tests.functional.pages import LogInPage, IndexPage, CmsIndexPage, TopicPage, SubtopicPage, MeasureEditPage, \
    MeasureCreatePage, RandomMeasure, MeasurePreviewPage, RandomDimension, DimensionAddPage, DimensionEditPage, \
    ChartBuilderPage, TableBuilderPage

import time

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_can_create_a_measure_page(driver, app,  test_app_editor, live_server,
                                   stub_topic_page, stub_subtopic_page):
    page = RandomMeasure()

    login(driver, live_server, test_app_editor)

    subtopic_page = SubtopicPage(driver, live_server, stub_topic_page, stub_subtopic_page)
    go_to_page(subtopic_page)

    '''
    CREATE A MEASURE
    '''
    create_measure(driver, live_server, page, stub_subtopic_page, stub_topic_page, subtopic_page)

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
    edit_measure_page.set_publication_date(page.publication_date)
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

    edit_dimension_page.set_suppression_rules(dimension.suppression_rules)
    edit_dimension_page.set_disclosure_control(dimension.disclosure_control)
    edit_dimension_page.click_update()

    assert edit_dimension_page.is_current()

    preview_measure_page.get()
    assert_page_contains(preview_measure_page, dimension.suppression_rules)
    assert_page_contains(preview_measure_page, dimension.disclosure_control)

    '''
    CREATE A SIMPLE CHART
    '''
    edit_dimension_page.get()
    assert edit_dimension_page.is_current()

    edit_dimension_page.click_create_chart()
    edit_dimension_page.wait_for_seconds(3)

    chart_builder_page = ChartBuilderPage(driver)

    chart_builder_page.paste_data(data=[['Ethnicity', 'Value'], ['White', '7'], ['BAME', '17']])
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.select_bar_chart_category('Ethnicity')
    chart_builder_page.click_preview()

    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.get()
    chart_builder_page.paste_data(data=[['Ethnicity', 'Gender', 'Value'],
                                        ['White', 'Male', '7'], ['BAME', 'Male', '17'],
                                        ['White', 'Female', '12'], ['BAME', 'Female', '19']])
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.select_bar_chart_category('Ethnicity')
    chart_builder_page.select_bar_chart_group('Gender')
    chart_builder_page.click_preview()

    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.select_chart_type('Panel bar chart')
    chart_builder_page.select_panel_bar_chart_primary('Ethnicity')
    chart_builder_page.select_panel_bar_chart_grouping('Gender')
    # chart_builder_page.click_preview()

    chart_builder_page.click_save()
    chart_builder_page.wait_for_seconds(1)

    chart_builder_page.click_back()

    '''
    CREATE A SIMPLE TABLE
    '''
    assert edit_dimension_page.is_current()
    edit_dimension_page.click_create_table()

    table_builder_page = TableBuilderPage(driver)
    assert table_builder_page.is_current()

    table_builder_page.paste_data(data=[['Ethnicity', 'Value'], ['White', '7'], ['BAME', '17']])

    table_builder_page.click_preview()

    table_builder_page.get()
    table_builder_page.paste_data(data=[['Ethnicity', 'Gender', 'Value'],
                                        ['White', 'Male', '7'], ['BAME', 'Male', '17'],
                                        ['White', 'Female', '12'], ['BAME', 'Female', '19']])
    table_builder_page.click_preview()
    table_builder_page.click_save()


def go_to_page(page):
    page.get()
    assert page.is_current()
    return page


def assert_page_contains(page, text):
    return page.source_contains(text)


def create_measure(driver, live_server, page, stub_subtopic_page, stub_topic_page, subtopic_page):
    subtopic_page.click_new_measure()
    create_measure_page = MeasureCreatePage(driver, live_server, stub_topic_page, stub_subtopic_page)
    create_measure_page.set_guid(page.guid)
    create_measure_page.set_title(page.title)
    create_measure_page.click_save()


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)

from random import shuffle

import pytest

from tests.functional.data_sets import inject_data, simple_data, ethnicity_by_time_data, ethnicity_by_gender_data, \
    granular_data, granular_with_parent_data
from tests.functional.pages import LogInPage, HomePage, TopicPage, MeasureEditPage, \
    MeasureCreatePage, DimensionAddPage, DimensionEditPage, \
    ChartBuilderPage, MinimalRandomMeasure, MinimalRandomDimension

pytestmark = pytest.mark.usefixtures('app', 'db_session', 'stub_measure_page')


def test_can_build_charts(driver, app, test_app_editor, live_server, stub_topic_page, stub_subtopic_page):
    page = MinimalRandomMeasure()

    chart_builder_page = construct_test_chart_builder_page(driver, live_server, page, stub_subtopic_page,
                                                           stub_topic_page, test_app_editor)

    run_bar_chart_scenarios(chart_builder_page, driver)

    run_line_graph_scenarios(chart_builder_page, driver)

    run_component_charts_scenarios(chart_builder_page, driver)

    run_grouped_bar_charts_scenarios(chart_builder_page, driver)

    run_panel_bar_charts_scenarios(chart_builder_page, driver)

    run_panel_line_graph_scenarios(chart_builder_page, driver)

    run_parent_child_bar_chart_scenarios(chart_builder_page, driver)


def construct_test_chart_builder_page(driver, live_server, page, stub_subtopic_page, stub_topic_page, test_app_editor):
    login(driver, live_server, test_app_editor)
    '''
    BROWSE TO POINT WHERE WE CAN ADD A MEASURE
    '''
    home_page = HomePage(driver, live_server)
    home_page.click_topic_link(stub_topic_page)
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)
    '''
    SET UP A SIMPLE DIMENSION WE CAN BUILD TEST CHARTS ON
    '''
    topic_page.click_add_measure(stub_subtopic_page)
    topic_page.wait_until_url_contains('/measure/new')
    create_measure(driver, live_server, page, stub_topic_page, stub_subtopic_page)
    topic_page.wait_until_url_contains('/edit')
    edit_measure_page = MeasureEditPage(driver)
    edit_measure_page.get()
    dimension = MinimalRandomDimension()
    edit_measure_page.click_add_dimension()
    edit_measure_page.wait_until_url_contains('/dimension/new')
    create_dimension_page = DimensionAddPage(driver)
    create_dimension_page.set_title(dimension.title)
    create_dimension_page.set_time_period(dimension.time_period)
    create_dimension_page.set_summary(dimension.summary)
    create_dimension_page.click_save()
    edit_dimension_page = DimensionEditPage(driver)
    edit_dimension_page.get()
    edit_dimension_page.wait_for_seconds(1)
    edit_dimension_page.click_create_chart()
    edit_dimension_page.wait_until_url_contains('create-chart')
    chart_builder_page = ChartBuilderPage(driver, edit_dimension_page)
    return chart_builder_page


def run_bar_chart_scenarios(chart_builder_page, driver):
    """
    SCENARIO 1. CREATE A SIMPLE CHART
    """

    '''
    GIVEN some basic data appropriate for building bar charts
    '''
    inject_data(driver, simple_data)
    chart_builder_page.click_data_okay()
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN the edit screen should get set up
    '''
    assert chart_builder_page.source_contains('5 rows by 2 columns')
    assert len(chart_builder_page.get_ethnicity_settings_list()) == 3
    assert chart_builder_page.get_ethnicity_settings_value() == "ONS 2011 - 5+1"

    '''
    WHEN we select bar chart
    '''
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN we should have a chart with ethnicities as the bars
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']

    values = chart_builder_page.chart_labels()
    assert values == ['5', '4', '3', '2', '1']

    '''
    WHEN we select an alternative ethnicity set up
    '''
    chart_builder_page.select_ethnicity_settings('ONS 2001 - 5+1')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN the ethnicities that appear in the charts get changed
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other inc Chinese']

    """
    SCENARIO 2. CREATE A CHART WITH DISORDERLY DATA
    """

    '''
    GIVEN a shuffled version of our simple data
    '''
    chart_builder_page.refresh()
    inject_data(driver, shuffle_table(simple_data))
    chart_builder_page.click_data_okay()

    '''
    WHEN we select bar chart
    '''
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN the ethnicities are correctly sorted automatically
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']
    return chart_builder_page


def run_parent_child_bar_chart_scenarios(chart_builder_page, driver):
    """
    SCENARIO 1. USING DATA THAT DOESN'T HAVE PARENT CATEGORIES
    """

    '''
    GIVEN a version of data that has low granularity but doesn't include
    '''
    chart_builder_page.refresh()
    inject_data(driver, granular_data)
    chart_builder_page.click_data_okay()

    '''
    WHEN we select bar chart
    '''
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN the ethnicities are correctly sorted automatically and include parents
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    actual = spaceless(ethnicities)
    expected = spaceless([
        'Asian', 'Bangladeshi', 'Indian', 'Pakistani', 'Asian other',
        'Black', 'Black African', 'Black Caribbean', 'Black other',
        'Mixed', 'Mixed White/Asian', 'Mixed White/Black African', 'Mixed White/Black Caribbean', 'Mixed other',
        'White', 'White British', 'White Irish', 'White other',
        'Other inc Chinese', 'Chinese', 'Any other'])

    assert actual == expected

    """
    SCENARIO 2. USING DATA THAT DOES HAVE PARENT CATEGORIES
    """

    '''
    GIVEN a version of data that has low granularity but doesn't include parents
    '''
    chart_builder_page.refresh()
    inject_data(driver, granular_with_parent_data)
    chart_builder_page.click_data_okay()

    '''
    WHEN we select bar chart
    '''
    chart_builder_page.select_chart_type('Bar chart')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN the ethnicities are correctly sorted automatically and include parents
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    actual = spaceless(ethnicities)
    expected = spaceless([
        'Asian', 'Bangladeshi', 'Indian', 'Pakistani', 'Asian other',
        'Black', 'Black African', 'Black Caribbean', 'Black other',
        'Mixed', 'Mixed White/Asian', 'Mixed White/Black African', 'Mixed White/Black Caribbean', 'Mixed other',
        'White', 'White British', 'White Irish', 'White other',
        'Other inc Chinese', 'Chinese', 'Any other'])
    assert actual == expected

    '''
    AND the parent bars are a different colour to child bars
    note: Asian (parent) = 0, Bangladeshi (child) = 1, Indian (child) = 2
    '''
    bar_colours = chart_builder_page.chart_bar_colours()
    assert bar_colours[0] != bar_colours[1]
    assert bar_colours[1] == bar_colours[2]


def run_grouped_bar_charts_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR CHARTS with ethnicity for sub-groups
    """
    '''
    GIVEN some basic data appropriate for building grouped bar charts
    '''
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_okay()
    '''
    WHEN we add basic grouped bar chart settings
    '''
    chart_builder_page.select_chart_type('Grouped bar chart')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_bar_data_style('Use ethnicity for sub-groups')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_groups_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN a grouped bar chart exists with ethnicities as bars and genders as groups
    '''
    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {'F', 'M'}
    ethnicities = chart_builder_page.chart_series()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']
    '''


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for sections
    '''
    '''
    WHEN we add basic component chart settings
    '''
    chart_builder_page.select_grouped_bar_data_style('Use ethnicity for major groups')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_bar_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN a component graph exists with two gender bars and ethnicity sections
    '''
    genders = set(chart_builder_page.chart_series())
    assert genders == {'F', 'M'}
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']


def run_component_charts_scenarios(chart_builder_page, driver):
    """


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for bars
    """
    '''
    GIVEN some basic data appropriate for building component charts
    '''
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_okay()
    '''
    WHEN we add basic component chart settings
    '''
    chart_builder_page.select_chart_type('Component chart')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_data_style('Use ethnicity for bars')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_section_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN a component graph exists with ethnicities as bars and genders for sections
    '''
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']
    genders = set(chart_builder_page.chart_series())
    assert genders == {'F', 'M'}
    '''


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for sections
    '''
    '''
    WHEN we add basic component chart settings
    '''
    chart_builder_page.select_component_data_style('Use ethnicity for bar sections')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_bar_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN a component graph exists with two gender bars and ethnicity sections
    '''
    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {'F', 'M'}
    ethnicities = chart_builder_page.chart_series()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']


def run_line_graph_scenarios(chart_builder_page, driver):
    '''

    CHART BUILDER CAN BUILD LINE GRAPHS
    '''
    '''
    GIVEN some basic data appropriate for building line graphs
    '''
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_time_data)
    chart_builder_page.click_data_okay()
    '''
    WHEN we add basic line chart settings
    '''
    chart_builder_page.select_chart_type('Line graph')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_line_x_axis_column('Time')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN a line graph exists with times on the x-axis and ethnicity names as the series
    '''
    times = chart_builder_page.chart_x_axis()
    assert times == ['1', '2', '3']
    ethnicities = chart_builder_page.graph_series()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']
    '''

    CHART BUILDER ORDERS LINE GRAPH SERIES according to presets
    '''
    '''
    GIVEN some shuffled up data appropriate for building line graphs
    '''
    chart_builder_page.refresh()
    inject_data(driver, shuffle_table(ethnicity_by_time_data))
    chart_builder_page.click_data_okay()
    '''
    WHEN we add basic line chart settings
    '''
    chart_builder_page.select_chart_type('Line graph')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_line_x_axis_column('Time')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN ethnicities are ordered as the series
    '''
    ethnicities = chart_builder_page.graph_series()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']


def run_panel_bar_charts_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR CHARTS with ethnicity for sub-groups
    """
    '''
    GIVEN some basic data appropriate for building panel bar charts
    '''
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_okay()
    '''
    WHEN we add basic panel bar chart settings
    '''
    chart_builder_page.select_chart_type('Panel bar chart')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_data_style('Use ethnicity for bars')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_panel_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings('ONS 2011 - 5+1')
    chart_builder_page.wait_for_seconds(1)
    '''
    THEN panel bar charts exists ethnicities as bars and with one panel for each gender
    '''
    genders = set(chart_builder_page.panel_names())
    assert genders == {'F', 'M'}

    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']

    '''
    CHART BUILDER CAN BUILD PANEL CHARTS with ethnicity for panels
    '''
    '''
    WHEN we add basic component chart settings
    '''
    chart_builder_page.select_panel_bar_data_style('Use ethnicity for panels')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_bar_column('Gender')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings('ONS 2011 - 5+1')
    chart_builder_page.wait_for_seconds(1)

    '''
    THEN panel bar charts exist with genders as bars and with one panel for each ethnicity
    '''
    ethnicities = chart_builder_page.panel_names()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']

    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {'M', 'F'}


def run_panel_line_graph_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD LINE GRAPHS
    """

    '''
    GIVEN some basic data appropriate for building line graphs
    '''
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_time_data)
    chart_builder_page.click_data_okay()
    '''
    WHEN we add panel line chart settings
    '''
    chart_builder_page.select_chart_type('Panel line chart')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_line_x_axis_column('Time')
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings('ONS 2011 - 5+1')
    chart_builder_page.wait_for_seconds(2)
    '''
    THEN a line graph exists with times on the x-axis and ethnicity names as the series

    note: highcharts optimises x-axes and particularly on panel line charts - we aren't going to check up on these
    '''
    ethnicities = chart_builder_page.panel_names()
    assert ethnicities == ['Asian', 'Black', 'Mixed', 'White', 'Other']


def spaceless(string_list):
    def despace(s):
        return "".join(s.split())

    return [despace(s) for s in string_list]


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


def shuffle_table(table):
    table_body = table[1:]
    shuffle(table_body)
    return [table[0]] + table_body

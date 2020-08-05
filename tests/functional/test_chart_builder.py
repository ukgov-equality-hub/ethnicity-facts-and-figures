from application.auth.models import TypeOfUser
from tests.functional.data_sets import (
    inject_data,
    simple_data,
    ethnicity_by_time_data,
    ethnicity_by_gender_data,
    granular_data,
    granular_with_parent_data,
)
from tests.functional.pages import (
    HomePage,
    TopicPage,
    MeasureEditPage,
    DimensionAddPage,
    DimensionEditPage,
    ChartBuilderPage,
    MinimalRandomDimension,
)
from tests.functional.utils import spaceless, login, shuffle_table, new_create_measure
from tests.models import MeasureVersionFactory, UserFactory


def test_can_build_charts(driver, app, live_server):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
    published_measure_version = MeasureVersionFactory(status="APPROVED")

    chart_builder_page = construct_test_chart_builder_page(driver, live_server, published_measure_version, rdu_user)

    run_bar_chart_scenarios(chart_builder_page, driver)

    run_line_chart_scenarios(chart_builder_page, driver)

    run_component_charts_scenarios(chart_builder_page, driver)

    run_grouped_bar_charts_scenarios(chart_builder_page, driver)

    run_panel_bar_charts_scenarios(chart_builder_page, driver)

    run_panel_line_chart_scenarios(chart_builder_page, driver)

    # TODO: figure out why this test is no longer working in recent
    # versions of Chrome / Chromedriver / Selenium
    # run_parent_child_bar_chart_scenarios(chart_builder_page, driver)

    run_save_and_load_scenario(chart_builder_page, driver)


def construct_test_chart_builder_page(driver, live_server, measure_version, rdu_user):
    login(driver, live_server, rdu_user)
    """
    BROWSE TO POINT WHERE WE CAN ADD A MEASURE
    """
    home_page = HomePage(driver, live_server)
    home_page.click_topic_link(measure_version.measure.subtopic.topic)
    topic_page = TopicPage(driver, live_server, measure_version.measure.subtopic.topic)
    topic_page.expand_accordion_for_subtopic(measure_version.measure.subtopic)
    """
    SET UP A SIMPLE DIMENSION WE CAN BUILD TEST CHARTS ON
    """
    topic_page.click_add_measure(measure_version.measure.subtopic)
    topic_page.wait_until_url_contains("/measure/new")
    new_create_measure(driver, live_server, measure_version)
    topic_page.wait_until_url_contains("/edit")
    edit_measure_page = MeasureEditPage(driver)
    edit_measure_page.get()
    dimension = MinimalRandomDimension()
    edit_measure_page.click_add_dimension()
    edit_measure_page.wait_until_url_contains("/dimension/new")
    create_dimension_page = DimensionAddPage(driver)
    create_dimension_page.set_title(dimension.title)
    create_dimension_page.set_time_period(dimension.time_period)
    create_dimension_page.set_summary(dimension.summary)
    create_dimension_page.click_save()
    edit_dimension_page = DimensionEditPage(driver)
    edit_dimension_page.get()
    edit_dimension_page.wait_for_seconds(1)
    edit_dimension_page.click_create_chart()
    edit_dimension_page.wait_until_url_contains("create-chart")
    chart_builder_page = ChartBuilderPage(driver, edit_dimension_page)
    return chart_builder_page


def run_save_and_load_scenario(chart_builder_page, driver):
    """
    Check that settings are retained on save
    """
    chart_builder_page.refresh()

    """
    GIVEN we build a basic chart
    """
    inject_data(driver, simple_data)
    chart_builder_page.click_data_ok()
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.click_edit_data()
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.click_data_cancel()
    chart_builder_page.select_chart_type("Bar chart")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the edit screen should setup with default classification (for simple data)
    """
    assert chart_builder_page.get_ethnicity_settings_code() == "5B"
    assert chart_builder_page.get_ethnicity_settings_value() == "ONS 2011 - 5+1"
    assert chart_builder_page.get_custom_classification_panel().is_displayed() is False

    """
    WHEN we select an alternate classification and save
    """
    chart_builder_page.select_ethnicity_settings_value("ONS 2001 - 5+1")

    assert chart_builder_page.get_ethnicity_settings_code() == "5A"
    assert chart_builder_page.get_ethnicity_settings_value() == "ONS 2001 - 5+1"

    chart_builder_page.click_save()
    chart_builder_page.wait_for_seconds(1)

    """
    THEN it should reload with the alternate settings
    """
    assert chart_builder_page.get_ethnicity_settings_code() == "5A"
    assert chart_builder_page.get_ethnicity_settings_value() == "ONS 2001 - 5+1"


def run_bar_chart_scenarios(chart_builder_page, driver):
    """
    SCENARIO 1. CREATE A SIMPLE CHART
    """

    """
    GIVEN some basic data appropriate for building bar charts
    """
    inject_data(driver, simple_data)
    chart_builder_page.click_data_ok()
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the edit screen should get set up
    """
    assert chart_builder_page.source_contains("5 rows by 2 columns")
    assert len(chart_builder_page.get_ethnicity_settings_list()) == 3
    assert chart_builder_page.get_ethnicity_settings_value() == "ONS 2011 - 5+1"
    assert chart_builder_page.get_custom_classification_panel().is_displayed() is False

    """
    WHEN we select bar chart
    """
    chart_builder_page.select_chart_type("Bar chart")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN we should have a chart with ethnicities as the bars
    """
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]

    values = chart_builder_page.chart_labels()
    assert values == ["5", "4", "3", "2", "1"]

    """
    WHEN we select an alternative ethnicity set up
    """
    chart_builder_page.select_ethnicity_settings("ONS 2001 - 5+1")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities that appear in the charts get changed
    """
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other including Chinese"]

    """
    SCENARIO 2. CREATE A CHART WITH DISORDERLY DATA
    """

    """
    GIVEN a shuffled version of our simple data
    """
    chart_builder_page.refresh()
    inject_data(driver, shuffle_table(simple_data))
    chart_builder_page.click_data_ok()

    """
    WHEN we select bar chart
    """
    chart_builder_page.select_chart_type("Bar chart")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities are correctly sorted automatically
    """
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]
    return chart_builder_page


def run_parent_child_bar_chart_scenarios(chart_builder_page, driver):
    """
    SCENARIO 1. USING DATA THAT DOESN'T HAVE PARENT CATEGORIES
    """

    """
    GIVEN a version of data that has low granularity but doesn't include
    """
    chart_builder_page.refresh()
    inject_data(driver, granular_data)
    chart_builder_page.click_data_ok()

    """
    WHEN we select bar chart
    """
    chart_builder_page.select_chart_type("Bar chart")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities are correctly sorted automatically and include parents
    """
    ethnicities = chart_builder_page.chart_x_axis()
    actual = spaceless(ethnicities)
    expected = spaceless(
        [
            "Asian",
            "Bangladeshi",
            "Indian",
            "Pakistani",
            "Asian other",
            "Black",
            "Black African",
            "Black Caribbean",
            "Black other",
            "Mixed",
            "Mixed White/Asian",
            "Mixed White/Black African",
            "Mixed White/Black Caribbean",
            "Mixed other",
            "White",
            "White British",
            "White Irish",
            "White other",
            "Other inc Chinese",
            "Chinese",
            "Any other",
        ]
    )

    assert actual == expected

    """
    SCENARIO 2. USING DATA THAT DOES HAVE PARENT CATEGORIES
    """

    """
    GIVEN a version of data that has low granularity but doesn't include parents
    """
    chart_builder_page.refresh()
    inject_data(driver, granular_with_parent_data)
    chart_builder_page.click_data_ok()

    """
    WHEN we select bar chart
    """
    chart_builder_page.select_chart_type("Bar chart")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities are correctly sorted automatically and include parents
    """
    ethnicities = chart_builder_page.chart_x_axis()
    actual = spaceless(ethnicities)
    expected = spaceless(
        [
            "Asian",
            "Bangladeshi",
            "Indian",
            "Pakistani",
            "Asian other",
            "Black",
            "Black African",
            "Black Caribbean",
            "Black other",
            "Mixed",
            "Mixed White/Asian",
            "Mixed White/Black African",
            "Mixed White/Black Caribbean",
            "Mixed other",
            "White",
            "White British",
            "White Irish",
            "White other",
            "Other inc Chinese",
            "Chinese",
            "Any other",
        ]
    )
    assert actual == expected

    """
    AND the parent bars are a different colour to child bars
    note: Asian (parent) = 0, Bangladeshi (child) = 1, Indian (child) = 2
    """
    bar_colours = chart_builder_page.chart_bar_colours()
    assert bar_colours[0] != bar_colours[1]
    assert bar_colours[1] == bar_colours[2]


def run_grouped_bar_charts_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR CHARTS with ethnicity for sub-groups
    """
    """
    GIVEN some basic data appropriate for building grouped bar charts
    """
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_ok()
    """
    WHEN we add basic grouped bar chart settings
    """
    chart_builder_page.select_chart_type("Grouped bar chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_bar_data_style("Use ethnicity for sub-groups")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_groups_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN a grouped bar chart exists with ethnicities as bars and genders as groups
    """
    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {"F", "M"}
    ethnicities = chart_builder_page.chart_series()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]
    """


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for sections
    """
    """
    WHEN we add basic component chart settings
    """
    chart_builder_page.select_grouped_bar_data_style("Use ethnicity for major groups")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_grouped_bar_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN a component graph exists with two gender bars and ethnicity sections
    """
    genders = set(chart_builder_page.chart_series())
    assert genders == {"F", "M"}
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]


def run_component_charts_scenarios(chart_builder_page, driver):
    """


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for bars
    """
    """
    GIVEN some basic data appropriate for building component charts
    """
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_ok()
    """
    WHEN we add basic component chart settings
    """
    chart_builder_page.select_chart_type("Component chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_data_style("Use ethnicity for bars")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_section_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN a component graph exists with ethnicities as bars and genders for sections
    """
    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]
    genders = set(chart_builder_page.chart_series())
    assert genders == {"F", "M"}
    """


    CHART BUILDER CAN BUILD COMPONENT CHARTS with ethnicity for sections
    """
    """
    WHEN we add basic component chart settings
    """
    chart_builder_page.select_component_data_style("Use ethnicity for bar sections")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_component_bar_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN a component graph exists with two gender bars and ethnicity sections
    """
    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {"F", "M"}
    ethnicities = chart_builder_page.chart_series()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]


def run_line_chart_scenarios(chart_builder_page, driver):
    """

    CHART BUILDER CAN BUILD LINE CHARTS
    """
    """
    GIVEN some basic data appropriate for building line charts
    """
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_time_data)
    chart_builder_page.click_data_ok()
    """
    WHEN we add basic line chart settings
    """
    chart_builder_page.select_chart_type("Line chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_line_x_axis_column("Time")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN a line chart exists with times on the x-axis and ethnicity names as the series
    """
    times = chart_builder_page.chart_x_axis()
    assert times == ["1", "2", "3"]
    ethnicities = chart_builder_page.graph_series()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]
    """

    CHART BUILDER ORDERS LINE CHART SERIES according to classifications
    """
    """
    GIVEN some shuffled up data appropriate for building line charts
    """
    chart_builder_page.refresh()
    inject_data(driver, shuffle_table(ethnicity_by_time_data))
    chart_builder_page.click_data_ok()
    """
    WHEN we add basic line chart settings
    """
    chart_builder_page.select_chart_type("Line chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_line_x_axis_column("Time")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN ethnicities are ordered as the series
    """
    ethnicities = chart_builder_page.graph_series()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]


def run_panel_bar_charts_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR CHARTS with ethnicity for sub-groups
    """
    """
    GIVEN some basic data appropriate for building panel bar charts
    """
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    chart_builder_page.click_data_ok()
    """
    WHEN we add basic panel bar chart settings
    """
    chart_builder_page.select_chart_type("Panel bar chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_data_style("Use ethnicity for bars")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_panel_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings("ONS 2011 - 5+1")
    chart_builder_page.wait_for_seconds(1)
    """
    THEN panel bar charts exists ethnicities as bars and with one panel for each gender
    """
    genders = set(chart_builder_page.panel_names())
    assert genders == {"F", "M"}

    ethnicities = chart_builder_page.chart_x_axis()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]

    """
    CHART BUILDER CAN BUILD PANEL CHARTS with ethnicity for panels
    """
    """
    WHEN we add basic component chart settings
    """
    chart_builder_page.select_panel_bar_data_style("Use ethnicity for panels")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_bar_bar_column("Gender")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings("ONS 2011 - 5+1")
    chart_builder_page.wait_for_seconds(1)

    """
    THEN panel bar charts exist with genders as bars and with one panel for each ethnicity
    """
    ethnicities = chart_builder_page.panel_names()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]

    genders = set(chart_builder_page.chart_x_axis())
    assert genders == {"M", "F"}


def run_panel_line_chart_scenarios(chart_builder_page, driver):
    """
    CHART BUILDER CAN BUILD LINE CHARTS
    """

    """
    GIVEN some basic data appropriate for building line charts
    """
    chart_builder_page.refresh()
    inject_data(driver, ethnicity_by_time_data)
    chart_builder_page.click_data_ok()
    """
    WHEN we add panel line chart settings
    """
    chart_builder_page.select_chart_type("Panel line chart")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_panel_line_x_axis_column("Time")
    chart_builder_page.wait_for_seconds(1)
    chart_builder_page.select_ethnicity_settings("ONS 2011 - 5+1")
    chart_builder_page.wait_for_seconds(2)
    """
    THEN a line chart exists with times on the x-axis and ethnicity names as the series

    note: highcharts optimises x-axes and particularly on panel line charts - we aren't going to check up on these
    """
    ethnicities = chart_builder_page.panel_names()
    assert ethnicities == ["Asian", "Black", "Mixed", "White", "Other"]

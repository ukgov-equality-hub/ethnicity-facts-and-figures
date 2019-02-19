from application.auth.models import TypeOfUser

from tests.functional.data_sets import inject_data, simple_data, ethnicity_by_gender_data
from tests.functional.pages import (
    HomePage,
    TopicPage,
    MeasureEditPage,
    DimensionAddPage,
    DimensionEditPage,
    TableBuilderPage,
    MinimalRandomDimension,
)
from tests.functional.utils import create_measure, driver_login, shuffle_table
from tests.models import UserFactory, MeasureVersionFactory


def test_can_build_tables(driver, app, live_server, government_departments, frequencies_of_release):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
    measure_version = MeasureVersionFactory(status="APPROVED")

    table_builder_page = construct_test_table_builder_page(driver, live_server, measure_version, rdu_user)

    run_simple_table_scenarios(table_builder_page, driver)

    run_complex_table_by_row_scenario(table_builder_page, driver)

    run_complex_table_by_column_scenario(table_builder_page, driver)

    run_save_and_load_scenario(table_builder_page, driver)


def construct_test_table_builder_page(driver, live_server, measure_version, rdu_user):
    driver_login(driver, live_server, rdu_user)
    """
    BROWSE TO POINT WHERE WE CAN ADD A MEASURE
    """
    home_page = HomePage(driver, live_server)
    home_page.click_topic_link(measure_version.measure.subtopic.topic)
    topic_page = TopicPage(driver, live_server, measure_version.measure.subtopic.topic)
    topic_page.expand_accordion_for_subtopic(measure_version.measure.subtopic)
    """
    SET UP A SIMPLE DIMENSION WE CAN BUILD TEST TABLES ON
    """
    topic_page.click_add_measure(measure_version.measure.subtopic)
    topic_page.wait_until_url_contains("/measure/new")
    create_measure(
        driver, live_server, measure_version, measure_version.measure.subtopic.topic, measure_version.measure.subtopic
    )
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
    edit_dimension_page.click_create_table()
    edit_dimension_page.wait_until_url_contains("create-table")
    table_builder_page = TableBuilderPage(driver)
    return table_builder_page


def run_save_and_load_scenario(table_builder_page, driver):
    """
    Check that settings are retained on save
    """
    table_builder_page.refresh()

    """
    GIVEN we build a basic table
    """
    inject_data(driver, simple_data)
    table_builder_page.click_data_ok()
    table_builder_page.wait_for_seconds(1)
    table_builder_page.click_data_edit()
    table_builder_page.wait_for_seconds(1)
    table_builder_page.click_data_cancel()
    table_builder_page.wait_for_seconds(1)

    """
    THEN the edit screen should setup with default classification (for simple data)
    """
    assert table_builder_page.get_ethnicity_settings_code() == "5B"
    assert table_builder_page.get_ethnicity_settings_value() == "ONS 2011 - 5+1"

    """
    WHEN we choose a column to display
    """
    table_builder_page.select_column(1, "Value")
    table_builder_page.wait_for_seconds(1)

    """
    AND we select an alternate classification and save
    """
    table_builder_page.select_ethnicity_settings_value("ONS 2001 - 5+1")

    assert table_builder_page.get_ethnicity_settings_code() == "5A"
    assert table_builder_page.get_ethnicity_settings_value() == "ONS 2001 - 5+1"

    table_builder_page.click_save()
    table_builder_page.wait_for_seconds(1)

    """
    THEN it should reload with the alternate settings
    """
    assert table_builder_page.get_ethnicity_settings_code() == "5A"
    assert table_builder_page.get_ethnicity_settings_value() == "ONS 2001 - 5+1"


def run_simple_table_scenarios(table_builder_page, driver):
    """
    SCENARIO 1. CREATE A SIMPLE TABLE
    """

    """
    GIVEN some basic data appropriate for building simple tables
    """
    inject_data(driver, simple_data)
    table_builder_page.click_data_ok()
    table_builder_page.wait_for_seconds(1)

    """
    THEN the edit screen should get set up
    """
    assert table_builder_page.source_contains("5 rows by 2 columns")
    assert len(table_builder_page.get_ethnicity_settings_list()) == 3
    assert table_builder_page.get_ethnicity_settings_value() == "ONS 2011 - 5+1"
    assert table_builder_page.input_index_column_name() == "Ethnicity"

    """
    THEN we select the column to display
    """
    table_builder_page.select_column(1, "Value")
    table_builder_page.wait_for_seconds(1)

    """
    THEN we should have a table with appropriate headers
    """
    assert table_builder_page.table_headers() == ["Ethnicity", "Value"]
    assert table_builder_page.table_index_column_name() == "Ethnicity"

    """
    AND we should have a table with appropriate column values
    """
    assert table_builder_page.table_column_contents(1) == ["Asian", "Black", "Mixed", "White", "Other"]
    assert table_builder_page.table_column_contents(2) == ["5", "4", "3", "2", "1"]

    """
    WHEN we select an alternative ethnicity set up
    """
    table_builder_page.select_ethnicity_settings_value("ONS 2001 - 5+1")
    table_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities that appear in the tables get changed
    """
    assert table_builder_page.table_column_contents(1) == ["Asian", "Black", "Mixed", "White", "Other inc Chinese"]

    """
    WHEN we select an alternative first column name
    """
    table_builder_page.set_input_index_column_name("Custom first column")
    table_builder_page.wait_for_seconds(1)

    """
    THEN the first column name in the table is changed
    """
    assert table_builder_page.table_index_column_name() == "Custom first column"

    """
    SCENARIO 2. CREATE A CHART WITH DISORDERLY DATA
    """

    """
    GIVEN a shuffled version of our simple data
    """
    table_builder_page.refresh()
    inject_data(driver, shuffle_table(simple_data))
    table_builder_page.click_data_ok()

    """
    THEN we select the column to display
    """
    table_builder_page.select_column(1, "Value")
    table_builder_page.wait_for_seconds(1)

    """
    THEN the ethnicities are correctly sorted automatically
    """
    assert table_builder_page.table_column_contents(1) == ["Asian", "Black", "Mixed", "White", "Other"]
    return table_builder_page


def run_complex_table_by_row_scenario(table_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR TABLES with ethnicity for sub-groups
    """
    """
    GIVEN some basic data appropriate for building grouped bar tables
    """
    table_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    table_builder_page.click_data_ok()

    """
    THEN first column names ought to be Ethnicity by default
    """
    assert table_builder_page.input_index_column_name() == "Ethnicity"

    """
    WHEN we set up the complex table options
    """
    table_builder_page.select_data_style("Use ethnicity for rows")
    table_builder_page.wait_for_seconds(1)
    table_builder_page.select_columns_when_ethnicity_is_row("Gender")
    table_builder_page.select_column(1, "Value")
    table_builder_page.select_column(2, "Gender")
    table_builder_page.wait_for_seconds(1)

    """
    THEN a complex table exists with ethnicities on the left, gender along the top, and sub-columns of value and gender.
    """
    assert table_builder_page.table_headers() == ["", "F", "M"]
    assert table_builder_page.table_secondary_headers() == ["Ethnicity", "Value", "Gender", "Value", "Gender"]
    assert table_builder_page.table_column_contents(1) == ["Asian", "Black", "Mixed", "White", "Other"]
    assert table_builder_page.table_column_contents(2) == ["4", "1", "5", "4", "2"]
    assert table_builder_page.table_column_contents(3) == ["F"] * 5
    assert table_builder_page.table_column_contents(4) == ["5", "4", "3", "2", "1"]
    assert table_builder_page.table_column_contents(5) == ["M"] * 5

    """
    AND a first column name set on the table as default
    """
    assert table_builder_page.table_index_column_name() == "Ethnicity"

    """
    WHEN we change the value of the first column in the input box
    """
    table_builder_page.set_input_index_column_name("Custom first column")

    """
    THEN it changes the value of the first column in the table
    """
    assert table_builder_page.table_index_column_name() == "Custom first column"


def run_complex_table_by_column_scenario(table_builder_page, driver):
    """
    CHART BUILDER CAN BUILD GROUPED BAR TABLES with ethnicity for sub-groups using ethnicity for column groups
    """
    """
    GIVEN some basic data appropriate for building grouped bar tables
    """
    table_builder_page.refresh()
    inject_data(driver, ethnicity_by_gender_data)
    table_builder_page.click_data_ok()

    """
    WHEN we set up the complex table options for a use ethnicity by column setup
    """
    table_builder_page.select_data_style("Use ethnicity for columns")
    table_builder_page.wait_for_seconds(1)
    table_builder_page.select_rows_when_ethnicity_is_columns("Gender")
    table_builder_page.select_column(1, "Value")
    table_builder_page.select_column(2, "Gender")
    table_builder_page.wait_for_seconds(1)

    """
    AND a complex table exists with ethnicities across the columns, gender on the left, and sub-columns of value
    and gender.
    """
    assert table_builder_page.table_headers() == ["", "Asian", "Black", "Mixed", "White", "Other"]
    assert table_builder_page.table_secondary_headers() == [
        "Gender",
        "Value",
        "Gender",
        "Value",
        "Gender",
        "Value",
        "Gender",
        "Value",
        "Gender",
        "Value",
        "Gender",
    ]
    assert table_builder_page.table_column_contents(1) == ["F", "M"]
    assert table_builder_page.table_column_contents(2) == ["4", "5"]
    assert table_builder_page.table_column_contents(3) == ["F", "M"]
    assert table_builder_page.table_column_contents(4) == ["1", "4"]
    assert table_builder_page.table_column_contents(5) == ["F", "M"]

    """
    AND the first column setting has changed to the name of the selected row column
    """
    assert table_builder_page.table_index_column_name() == "Gender"
    assert table_builder_page.input_index_column_name() == "Gender"

    """
    WHEN we change to an ethnicity is rows setup
    """
    table_builder_page.select_data_style("Use ethnicity for rows")
    # table_builder_page.wait_for_seconds(1)
    table_builder_page.select_columns_when_ethnicity_is_row("Gender")
    # table_builder_page.wait_for_seconds(1)

    """
    THEN the first column reverts to ethnicity
    """
    assert table_builder_page.table_index_column_name() == "Ethnicity"
    assert table_builder_page.input_index_column_name() == "Ethnicity"

    """
    WHEN we change back to the ethnicity is columns setup
    """
    table_builder_page.select_data_style("Use ethnicity for columns")

    """
    THEN the first column reverts to gender
    """
    assert table_builder_page.table_index_column_name() == "Gender"
    assert table_builder_page.input_index_column_name() == "Gender"

    """
    WHEN we change the value of the first column in the input box
    """
    table_builder_page.set_input_index_column_name("Custom first column")

    """
    THEN it changes the value of the first column in the table
    """
    assert table_builder_page.table_index_column_name() == "Custom first column"

    """
    WHEN we change back to the ethnicity is rows setup
    """
    table_builder_page.select_data_style("Use ethnicity for rows")

    """
    THEN the first column name does not change
    """
    assert table_builder_page.table_index_column_name() == "Custom first column"
    assert table_builder_page.input_index_column_name() == "Custom first column"

    """
    WHEN we change back to the ethnicity is columns setup
    """
    table_builder_page.select_data_style("Use ethnicity for columns")

    """
    THEN the first column name does not change
    """
    assert table_builder_page.table_index_column_name() == "Custom first column"
    assert table_builder_page.input_index_column_name() == "Custom first column"

from application.auth.models import TypeOfUser

from tests.functional.data_sets import inject_data, simple_data, ethnicity_by_gender_data
from tests.functional.pages import (
    HomePage,
    TopicPage,
    MeasureEditPage,
    MeasurePreviewPage,
    RandomDimension,
    DimensionAddPage,
    DimensionEditPage,
    TableBuilderPage,
)
from tests.functional.utils import driver_login, assert_page_contains, create_measure
from tests.models import MeasureVersionFactory, UserFactory


def test_can_create_a_measure_page(driver, app, live_server):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)
    measure_version = MeasureVersionFactory(status="APPROVED")

    driver_login(driver, live_server, rdu_user)

    """
    BROWSE TO POINT WHERE WE CAN ADD A MEASURE
    """
    home_page = HomePage(driver, live_server)
    home_page.click_topic_link(measure_version.measure.subtopic.topic)

    topic_page = TopicPage(driver, live_server, measure_version.measure.subtopic.topic)
    topic_page.expand_accordion_for_subtopic(measure_version.measure.subtopic)

    """
    CREATE A NEW MEASURE
    """
    topic_page.click_add_measure(measure_version.measure.subtopic)
    topic_page.wait_until_url_contains("/measure/new")
    create_measure(
        driver, live_server, measure_version, measure_version.measure.subtopic.topic, measure_version.measure.subtopic
    )

    """
    EDIT THE MEASURE
    """
    topic_page.wait_until_url_contains("/edit")
    edit_measure_page = MeasureEditPage(driver)

    edit_measure_page.set_measure_summary(measure_version.measure_summary)
    edit_measure_page.set_summary(measure_version.summary)
    edit_measure_page.click_save()
    assert edit_measure_page.is_current()

    """
    PREVIEW CURRENT PROGRESS
    """
    edit_measure_page.click_preview()
    edit_measure_page.wait_until_url_does_not_contain("/cms/")

    preview_measure_page = MeasurePreviewPage(driver)
    assert preview_measure_page.is_current()

    assert_page_contains(preview_measure_page, measure_version.title)
    assert_page_contains(preview_measure_page, measure_version.measure_summary)
    assert_page_contains(preview_measure_page, measure_version.summary)

    """
    ADD A DIMENSION
    Save some dimension data
    """
    edit_measure_page.get()
    assert edit_measure_page.is_current()

    dimension = RandomDimension()

    edit_measure_page.click_add_dimension()
    edit_measure_page.wait_until_url_contains("/dimension/new")

    create_dimension_page = DimensionAddPage(driver)

    create_dimension_page.set_title(dimension.title)
    create_dimension_page.set_time_period(dimension.time_period)
    create_dimension_page.set_summary(dimension.summary)
    create_dimension_page.click_save()

    edit_dimension_page = DimensionEditPage(driver)
    assert edit_dimension_page.is_current()

    preview_measure_page.get()
    edit_dimension_page.wait_until_url_does_not_contain("/cms/")
    assert_page_contains(preview_measure_page, dimension.title)
    assert_page_contains(preview_measure_page, dimension.time_period)
    assert_page_contains(preview_measure_page, dimension.summary)

    """
    EDIT A DIMENSION
    """
    edit_dimension_page.get()
    assert edit_dimension_page.is_current()

    edit_dimension_page.set_summary("some updated text")
    edit_dimension_page.click_update()

    assert edit_dimension_page.is_current()

    preview_measure_page.get()
    edit_dimension_page.wait_until_url_does_not_contain("/cms/")
    assert_page_contains(preview_measure_page, "some updated text")

    """
    CHART BUILDER
    test content has been moved to a separate set of functional tests
    """

    """
    CREATE A SIMPLE TABLE
    """
    edit_dimension_page.get()
    assert edit_dimension_page.is_current()
    edit_dimension_page.click_create_table()
    edit_dimension_page.wait_until_url_contains("create-table")

    table_builder_page = TableBuilderPage(driver)
    assert table_builder_page.is_current()

    inject_data(driver, simple_data)
    table_builder_page.click_data_ok()
    table_builder_page.select_column(1, "Value")
    table_builder_page.click_save()
    table_builder_page.wait_for_seconds(1)

    """
    CREATE A TABLE WITH TWO COLUMNS
    """
    table_builder_page.get()
    table_builder_page.click_data_edit()
    inject_data(driver, ethnicity_by_gender_data)
    table_builder_page.click_data_ok()

    table_builder_page.select_data_style("Use ethnicity for rows")
    table_builder_page.select_columns_when_ethnicity_is_row("Gender")
    table_builder_page.select_column(1, "Value")
    table_builder_page.select_column(2, "Gender")

    table_builder_page.click_save()

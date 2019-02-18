from tests.functional.data_sets import inject_data, simple_data, ethnicity_by_gender_data
from tests.functional.pages import (
    LogInPage,
    HomePage,
    TopicPage,
    MeasureEditPage,
    MeasureCreatePage,
    MeasurePreviewPage,
    RandomDimension,
    DimensionAddPage,
    DimensionEditPage,
    TableBuilderPage,
)
from tests.models import MeasureVersionFactory


def test_can_create_a_measure_page(driver, app, test_app_editor, live_server, db_session):
    measure_version = MeasureVersionFactory(status="APPROVED")

    # Need to commit explicitly because functional tests run in a separate process with a separate session/transaction
    db_session.session.commit()

    login(driver, live_server, test_app_editor)

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

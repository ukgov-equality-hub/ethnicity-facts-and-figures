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
from tests.functional.utils import (
    driver_login,
    click_link_with_text,
    fill_in,
    click_button_with_text,
    assert_page_contains,
    create_measure,
)
from tests.models import (
    MeasureVersionFactory,
    UserFactory,
    DataSourceFactory,
    TopicFactory,
    SubtopicFactory,
    MeasureFactory,
)


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


def test_adding_an_existing_data_source(driver, app, live_server):

    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=True)

    topic = TopicFactory.create(title="Police and crime")
    subtopic = SubtopicFactory.create(title="Policing", topic=topic)
    DataSourceFactory.create(title="Police statistics 2019")

    existing_measure = MeasureFactory.create(subtopics=[subtopic])
    MeasureVersionFactory.create(status="APPROVED", measure=existing_measure)

    driver_login(driver, live_server, rdu_user)
    home_page = HomePage(driver, live_server)

    home_page.click_topic_link(topic)

    topic_page = TopicPage(driver, live_server, topic)
    topic_page.expand_accordion_for_subtopic(subtopic)

    topic_page.click_add_measure(subtopic)

    create_measure_page = MeasureEditPage(driver)
    create_measure_page.set_title("Arrests")
    create_measure_page.click_save()

    create_measure_page.click_add_primary_data_source()

    fill_in(driver, label_text="Search for an existing data source", with_text="Police statistics")
    click_button_with_text(driver, "Search")

    label_for_existing_data_source = driver.find_element_by_xpath("//label[text()='Police statistics 2019']")

    label_for_existing_data_source.click()

    click_button_with_text(driver, "Select")

    assert "Successfully added the data source ’Police statistics 2019’" in driver.page_source

    click_link_with_text(driver, "Preview this version")

    assert "Police statistics 2019" in driver.page_source

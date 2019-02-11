from flask import url_for

from application.data.dimensions import DimensionObjectBuilder
from application.utils import write_dimension_csv
from application.cms.models import UKCountry
from tests.models import MeasureVersionWithDimensionFactory, ClassificationFactory, DataSourceFactory
from tests.test_data.chart_and_table import simple_table, grouped_table


def test_table_object_builder_does_build_object_from_simple_table():
    measure_version = MeasureVersionWithDimensionFactory(dimensions__table=simple_table())
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the simple table
    assert table_object is not None
    assert table_object.get("table").get("title") == "Title of simple table"


def test_table_object_builder_does_build_object_from_grouped_table():
    measure_version = MeasureVersionWithDimensionFactory(dimensions__table=grouped_table())
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the grouped table
    assert table_object is not None
    assert table_object.get("table").get("title") == "Title of grouped table"


def test_table_object_builder_does_build_with_page_level_data_from_simple_table():
    data_source = DataSourceFactory(
        title="DWP Stats", source_url="http://dwp.gov.uk", publisher__name="Department for Work and Pensions"
    )
    measure_version = MeasureVersionWithDimensionFactory(
        title="Test Measure Page",
        guid="test-measure-page-guid",
        slug="test-measure-page-slug",
        area_covered=[UKCountry.ENGLAND],
        data_sources=[data_source],
        dimensions__table=simple_table(),
    )
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page-guid"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page-slug"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_dimension_object_builder_does_build_with_page_level_data_from_grouped_table():
    data_source = DataSourceFactory(
        title="DWP Stats", source_url="http://dwp.gov.uk", publisher__name="Department for Work and Pensions"
    )
    measure_version = MeasureVersionWithDimensionFactory(
        title="Test Measure Page",
        guid="test-measure-page-guid",
        slug="test-measure-page-slug",
        area_covered=[UKCountry.ENGLAND],
        data_sources=[data_source],
        dimensions__table=grouped_table(),
    )
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page-guid"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page-slug"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_table_object_builder_does_build_with_dimension_level_data_from_simple_table():
    measure_version = MeasureVersionWithDimensionFactory(
        title="Test Measure Page",
        guid="test-measure-page-guid",
        slug="test-measure-page-slug",
        area_covered=[UKCountry.ENGLAND],
        dimensions__title="Dimension title",
        dimensions__guid="dimension-guid",
        dimensions__time_period="dimension-time-period",
        dimensions__table=simple_table(),
    )
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "Dimension title"
    assert dimension_object["context"]["guid"] == "dimension-guid"
    assert dimension_object["context"]["time_period"] == "dimension-time-period"


def test_table_object_builder_does_build_with_dimension_level_data_from_grouped_table():
    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="Dimension title",
        dimensions__guid="dimension-guid",
        dimensions__time_period="dimension-time-period",
        dimensions__table=grouped_table(),
    )
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = measure_version.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "Dimension title"
    assert dimension_object["context"]["guid"] == "dimension-guid"
    assert dimension_object["context"]["time_period"] == "dimension-time-period"


def test_if_dimension_has_chart_download_chart_source_data(mock_logged_in_rdu_user, test_app_client):
    from tests.test_data.chart_and_table import chart, chart_source_data

    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="Dimension title",
        dimensions__chart=chart,
        dimensions__chart_source_data=chart_source_data,
        dimensions__chart_2_source_data=chart_source_data,
        dimensions__dimension_chart__classification=ClassificationFactory(id="2A"),
        dimensions__dimension_chart__includes_parents=False,
        dimensions__dimension_chart__includes_all=True,
        dimensions__dimension_chart__includes_unknown=False,
        # No table
        dimensions__dimension_table=None,
    )

    # GIVEN
    # we have a dimension with only chart data
    dimension = measure_version.dimensions[0]

    resp = test_app_client.get(
        url_for(
            "static_site.dimension_file_download",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=dimension.guid,
        )
    )
    d = DimensionObjectBuilder.build(dimension)

    # WHEN
    # we generate a plain table csv
    expected_csv = write_dimension_csv(dimension=d)

    # THEN
    # we get a return
    assert resp.status_code == 200
    assert resp.content_type == "text/csv"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="dimension-title.csv"'

    # from the data in the chart
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv


def test_if_dimension_has_chart_and_table_download_table_source_data(mock_logged_in_rdu_user, test_app_client):
    from tests.test_data.chart_and_table import chart, chart_source_data, table, table_source_data

    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="Dimension title",
        # Chart
        dimensions__chart=chart,
        dimensions__chart_source_data=chart_source_data,
        dimensions__chart_2_source_data=chart_source_data,
        dimensions__dimension_chart__classification=ClassificationFactory(id="2A"),
        dimensions__dimension_chart__includes_parents=False,
        dimensions__dimension_chart__includes_all=True,
        dimensions__dimension_chart__includes_unknown=False,
        # Table
        dimensions__table=table,
        dimensions__table_source_data=table_source_data,
        dimensions__table_2_source_data=table_source_data,
        dimensions__dimension_table__classification=ClassificationFactory(id="5A"),
        dimensions__dimension_table__includes_parents=True,
        dimensions__dimension_table__includes_all=False,
        dimensions__dimension_table__includes_unknown=True,
    )

    # GIVEN
    # we have a dimension with table and chart data
    dimension = measure_version.dimensions[0]

    resp = test_app_client.get(
        url_for(
            "static_site.dimension_file_download",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=dimension.guid,
        )
    )

    # WHEN
    # we generate a plain table csv
    d = DimensionObjectBuilder.build(dimension)
    expected_csv = write_dimension_csv(dimension=d)

    # THEN
    # we get a return
    assert resp.status_code == 200
    assert resp.content_type == "text/csv"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="dimension-title.csv"'

    # from the data in the table (not chart)
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv

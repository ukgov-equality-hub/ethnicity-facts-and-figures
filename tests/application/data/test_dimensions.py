from flask import url_for

from application.data.dimensions import DimensionObjectBuilder
from application.utils import write_dimension_csv


def test_table_object_builder_does_build_object_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the simple table
    assert table_object is not None


def test_table_object_builder_does_build_object_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    table_object = builder.build(dimension)

    # then the header for the returned table should match the ones from the simple table
    assert table_object is not None


def test_table_object_builder_does_build_with_page_level_data_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_dimension_object_builder_does_build_with_page_level_data_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the measure level info should be brought through
    assert dimension_object["context"]["measure"] == "Test Measure Page"
    assert dimension_object["context"]["measure_guid"] == "test-measure-page"
    assert dimension_object["context"]["measure_slug"] == "test-measure-page"
    assert dimension_object["context"]["location"] == "England"
    assert dimension_object["context"]["title"] == "DWP Stats"
    assert dimension_object["context"]["source_url"] == "http://dwp.gov.uk"
    assert dimension_object["context"]["publisher"] == "Department for Work and Pensions"


def test_table_object_builder_does_build_with_dimension_level_data_from_simple_table(stub_page_with_simple_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_simple_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "stub dimension"
    assert dimension_object["context"]["guid"] == "stub_dimension"
    assert dimension_object["context"]["time_period"] == "stub_timeperiod"


def test_table_object_builder_does_build_with_dimension_level_data_from_grouped_table(stub_page_with_grouped_table):
    # given - a table without a category_caption value
    builder = DimensionObjectBuilder()
    dimension = stub_page_with_grouped_table.dimensions[0]

    # when we process the object
    dimension_object = builder.build(dimension)

    # then the dimension level info should be brought through
    assert dimension_object["context"]["dimension"] == "stub dimension"
    assert dimension_object["context"]["guid"] == "stub_dimension"
    assert dimension_object["context"]["time_period"] == "stub_timeperiod"


def test_if_dimension_has_chart_download_chart_source_data(
    app, mock_rdu_user, test_app_client, stub_topic_page, stub_subtopic_page, stub_page_with_dimension_and_chart
):

    # GIVEN
    # we have a dimension with only chart data
    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    with test_app_client:

        test_app_client.post(url_for("security.login"), data={"email": mock_rdu_user.email, "password": "password123"})

        resp = test_app_client.get(
            url_for(
                "static_site.dimension_file_download",
                topic_slug=stub_topic_page.slug,
                subtopic_slug=stub_subtopic_page.slug,
                measure_slug=stub_page_with_dimension_and_chart.slug,
                version=stub_page_with_dimension_and_chart.version,
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
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

    # from the data in the chart
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv


def test_if_dimension_has_chart_and_table_download_table_source_data(
    app,
    mock_rdu_user,
    test_app_client,
    stub_topic_page,
    stub_subtopic_page,
    stub_page_with_dimension_and_chart_and_table,
):
    # GIVEN
    # we have a dimension with table and chart data
    dimension = stub_page_with_dimension_and_chart_and_table.dimensions[0]

    with test_app_client:

        test_app_client.post(url_for("security.login"), data={"email": mock_rdu_user.email, "password": "password123"})

        resp = test_app_client.get(
            url_for(
                "static_site.dimension_file_download",
                topic_slug=stub_topic_page.slug,
                subtopic_slug=stub_subtopic_page.slug,
                measure_slug=stub_page_with_dimension_and_chart_and_table.slug,
                version=stub_page_with_dimension_and_chart_and_table.version,
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
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

    # from the data in the table (not chart)
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv

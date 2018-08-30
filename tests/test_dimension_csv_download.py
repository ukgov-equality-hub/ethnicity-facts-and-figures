from flask import url_for

from application.data.dimensions import DimensionObjectBuilder
from application.utils import write_dimension_csv


# This unit contains tests for write_dimension_csv to ensure it is returning correct data and from
# the correct sources
#
# It does not test write_dimension_tabular_csv


def test_if_dimension_has_chart_download_chart_source_data(
    app, mock_user, test_app_client, stub_topic_page, stub_subtopic_page, stub_page_with_dimension_and_chart
):

    # GIVEN
    # we have a dimension with only chart data
    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    with test_app_client:

        test_app_client.post(url_for("security.login"), data={"email": mock_user.email, "password": "password123"})

        resp = test_app_client.get(
            url_for(
                "static_site.dimension_file_download",
                topic=stub_topic_page.uri,
                subtopic=stub_subtopic_page.uri,
                measure=stub_page_with_dimension_and_chart.uri,
                version=stub_page_with_dimension_and_chart.version,
                dimension=dimension.guid,
            )
        )
        d = DimensionObjectBuilder.build(dimension)

        # WHEN
        # we generate a plain table csv
        expected_csv = write_dimension_csv(dimension=d)

    # THEN
    # we get a return
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

    # from the data in the chart
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv


def test_if_dimension_has_chart_and_table_download_table_source_data(
    app, mock_user, test_app_client, stub_topic_page, stub_subtopic_page, stub_page_with_dimension_and_chart_and_table
):
    # GIVEN
    # we have a dimension with table and chart data
    dimension = stub_page_with_dimension_and_chart_and_table.dimensions[0]

    with test_app_client:

        test_app_client.post(url_for("security.login"), data={"email": mock_user.email, "password": "password123"})

        resp = test_app_client.get(
            url_for(
                "static_site.dimension_file_download",
                topic=stub_topic_page.uri,
                subtopic=stub_subtopic_page.uri,
                measure=stub_page_with_dimension_and_chart_and_table.uri,
                version=stub_page_with_dimension_and_chart_and_table.version,
                dimension=dimension.guid,
            )
        )

        # WHEN
        # we generate a plain table csv
        d = DimensionObjectBuilder.build(dimension)
        expected_csv = write_dimension_csv(dimension=d)

    # THEN
    # we get a return
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

    # from the data in the table (not chart)
    actual_data = resp.data.decode("utf-8")
    assert actual_data == expected_csv

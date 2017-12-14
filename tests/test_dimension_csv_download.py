from flask import url_for

from application.cms.data_utils import DimensionObjectBuilder
from application.utils import write_dimension_csv, write_dimension_tabular_csv


def test_if_dimension_has_chart_download_chart_source_data(app,
                                                           mock_user,
                                                           test_app_client,
                                                           stub_topic_page,
                                                           stub_subtopic_page,
                                                           stub_page_with_dimension_and_chart):

    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    with test_app_client:

        test_app_client.post(url_for('security.login'), data={'email': mock_user.email, 'password': 'password123'})

        resp = test_app_client.get(url_for('static_site.dimension_file_download',
                                           topic=stub_topic_page.uri,
                                           subtopic=stub_subtopic_page.uri,
                                           measure=stub_page_with_dimension_and_chart.uri,
                                           version=stub_page_with_dimension_and_chart.version,
                                           dimension=dimension.guid))

        d = DimensionObjectBuilder.build(dimension)
        expected_csv = write_dimension_csv(dimension=d)

    assert resp.status_code == 200
    assert resp.headers['Content-Disposition'] == 'attachment; filename="stub-dimension.csv"'

    actual_data = resp.data.decode('utf-8')

    assert actual_data == expected_csv


# def test_if_dimension_has_chart_and_table_download_table_source_data(app,
#                                                                      mock_user,
#                                                                      test_app_client,
#                                                                      stub_topic_page,
#                                                                      stub_subtopic_page,
#                                                                      stub_page_with_dimension_and_chart_and_table):
#
#     dimension = stub_page_with_dimension_and_chart_and_table.dimensions[0]
#
#     with test_app_client:
#
#         test_app_client.post(url_for('security.login'), data={'email': mock_user.email, 'password': 'password123'})
#
#         resp = test_app_client.get(url_for('static_site.dimension_file_download',
#                                            topic=stub_topic_page.uri,
#                                            subtopic=stub_subtopic_page.uri,
#                                            measure=stub_page_with_dimension_and_chart_and_table.uri,
#                                            version=stub_page_with_dimension_and_chart_and_table.version,
#                                            dimension=dimension.guid))
#
#         d = DimensionObjectBuilder.build(dimension)
#         expected_csv = write_dimension_tabular_csv(dimension=d)
#
#     assert resp.status_code == 200
#     assert resp.headers['Content-Disposition'] == 'attachment; filename="stub_dimension.csv"'
#
#     actual_data = resp.data.decode('utf-8')
#
#     assert actual_data == expected_csv

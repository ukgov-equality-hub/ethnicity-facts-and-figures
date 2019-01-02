import pytest
import re
from bs4 import BeautifulSoup


class TestMeasurePage:
    """
    This class includes a set of tests that check download links for source data of a measure page.
    Unfortunately, without a refactor of how dimensions are passed into the measure page template, we aren't
    able to test how the static site renders these links. The static site builder passes in a specially-formatted
    set of dimensions that aren't available in 'static-mode style requests' to the CMS.

    Tech improvement ticket: https://trello.com/c/U4rMSk0w/70
    """

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/test/example/test-measure-page/1.0/dimension/stub_dimension/tabular-download"),
        ),
    )
    def test_measure_page_download_table_tabular_data_link_correct(
        self,
        test_app_client,
        mock_logged_in_rdu_user,
        stub_page_with_upload_and_dimension_and_chart_and_table,
        static_mode,
        expected_url,
    ):
        resp = test_app_client.get(
            f"/test/example/test-measure-page/latest?static_mode={static_mode}", follow_redirects=False
        )
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        data_links = page.findAll("a", href=True, text="Download table data (CSV)")
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/test/example/test-measure-page/1.0/dimension/stub_dimension/download"),
        ),
    )
    def test_measure_page_download_table_source_data_link_correct(
        self,
        test_app_client,
        mock_logged_in_rdu_user,
        stub_page_with_upload_and_dimension_and_chart_and_table,
        static_mode,
        expected_url,
    ):
        resp = test_app_client.get(
            f"/test/example/test-measure-page/latest?static_mode={static_mode}", follow_redirects=False
        )
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        data_links = page.findAll("a", href=True, text="Source data (CSV)")
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

    @pytest.mark.parametrize(
        "static_mode, expected_url",
        (
            # ("yes", "<some_url>"),
            ("no", "/test/example/test-measure-page/1.0/downloads/test-measure-page-data.csv"),
        ),
    )
    def test_measure_page_download_measure_source_data_link_correct(
        self,
        test_app_client,
        mock_logged_in_rdu_user,
        stub_page_with_upload_and_dimension_and_chart_and_table,
        static_mode,
        expected_url,
    ):
        resp = test_app_client.get("/test/example/test-measure-page/latest", follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        data_links = page.findAll("a", href=True, text=re.compile(r"Test measure page data\s+-\s+Spreadsheet"))
        assert len(data_links) == 1
        assert data_links[0].attrs["href"] == expected_url

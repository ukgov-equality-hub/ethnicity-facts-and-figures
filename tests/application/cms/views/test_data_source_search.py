import pytest
from bs4 import BeautifulSoup
from lxml import html

from tests.models import DataSourceFactory, MeasureVersionFactory

from tests.utils import find_input_for_label_with_text
from flaky import flaky


class TestSearchDataSourceView:
    def __search_url(self, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit/data-sources"

    @flaky(max_runs=10, min_passes=1)
    def test_no_search_param_specified(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        response = test_app_client.get(self.__search_url(measure_version))
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Search for an existing data source" == page.find("title").text
        assert "Search for an existing data source" == page.find("h1").text.strip()

        input_field = find_input_for_label_with_text(page, "Search for an existing data source")

        assert input_field["value"] == ""

    @flaky(max_runs=10, min_passes=1)
    def test_search_param_specified(self, test_app_client, logged_in_rdu_user):

        DataSourceFactory.create(title="Annual population survey", publication_date="25 October 2018")
        measure_version = MeasureVersionFactory.create()

        response = test_app_client.get(self.__search_url(measure_version) + "?q=population")
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Search for an existing data source" == page.find("title").text
        assert "Search for an existing data source" == page.find("h1").text.strip()

        input_field = find_input_for_label_with_text(page, "Search for an existing data\u00A0source")

        assert input_field["value"] == "population"

        assert "Annual population survey" in page.text
        assert "25 October 2018" in page.text

    @flaky(max_runs=10, min_passes=1)
    def test_data_sources_already_linked_to_measure_version_are_excluded(self, test_app_client, logged_in_admin_user):
        measure_version = MeasureVersionFactory(data_sources__title="Data source 1")
        DataSourceFactory(title="Data source 2")
        DataSourceFactory(title="Data source 3")

        response = test_app_client.get(self.__search_url(measure_version) + "?q=data")
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        with pytest.raises(Exception):
            find_input_for_label_with_text(page, "Data source 1")

        assert find_input_for_label_with_text(page, "Data source 2")
        assert find_input_for_label_with_text(page, "Data source 3")

    @flaky(max_runs=10, min_passes=1)
    def test_search_returning_zero_results_shows_no_results_message_and_link_to_create_data_source(
        self, test_app_client, logged_in_admin_user
    ):
        measure_version = MeasureVersionFactory(data_sources__title="Data source 1")
        DataSourceFactory(title="Data source 2")
        DataSourceFactory(title="Data source 3")

        response = test_app_client.get(
            self.__search_url(measure_version) + "?q=definitely-not-going-to-appear-in-a-data-source"
        )
        doc = html.fromstring(response.get_data(as_text=True))

        assert (
            "No results found. Try again with different words or a less specific search, or create a new data source."
            in response.get_data(as_text=True)
        )

        assert doc.xpath("//a[text()='Create a new data source']")

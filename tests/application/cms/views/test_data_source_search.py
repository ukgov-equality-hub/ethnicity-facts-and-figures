from bs4 import BeautifulSoup

from tests.models import DataSourceFactory, MeasureVersionFactory

from tests.utils import find_input_for_label_with_text


class TestAddDataSourceView:
    def __search_url(self, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit/data-sources"

    def test_no_search_param_specified(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        response = test_app_client.get(self.__search_url(measure_version))
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Search for an existing data source" == page.find("title").text
        assert "Search for an existing data source" == page.find("h1").text.strip()

        input_field = find_input_for_label_with_text(page, "Search for an existing data source")

        assert input_field["value"] == ""

    def test_search_param_specified(self, test_app_client, logged_in_rdu_user):

        DataSourceFactory.create(title="Annual population survey", publication_date="25 October 2018")
        measure_version = MeasureVersionFactory.create()

        response = test_app_client.get(self.__search_url(measure_version) + "?q=population")
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Search for an existing data source" == page.find("title").text
        assert "Search for an existing data source" == page.find("h1").text.strip()

        input_field = find_input_for_label_with_text(page, "Search for an existing data source")

        assert input_field["value"] == "population"

        assert "Annual population survey" in page.text
        assert "25 October 2018" in page.text

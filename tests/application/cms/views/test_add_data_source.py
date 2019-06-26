from bs4 import BeautifulSoup

import re

from application.cms.models import DataSource, MeasureVersion

from tests.models import DataSourceFactory, MeasureVersionFactory

from tests.utils import find_input_for_label_with_text


class TestAddDataSourceView:
    def __get_page(self, measure_version_id, test_app_client):

        response = test_app_client.get(f"/cms/data-sources/new?measure_version_id={measure_version_id}")

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def test_returns_200_if_measure_version_set(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        response, _ = self.__get_page(measure_version.id, test_app_client)
        assert response.status_code == 200

    def test_page_title_if_measure_version_set(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        response, page = self.__get_page(measure_version.id, test_app_client)
        assert "Add data source" == page.find("h1").text
        assert "Add data source" == page.find("title").text

    def test_returns_400_if_measure_version_no_set(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.get("/cms/data-sources/new")
        assert response.status_code == 400

    def test_returns_400_if_measure_version_is_invalid(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.get("/cms/data-sources/new?measure_version_id=999999999")
        assert response.status_code == 400


class TestCreateDataSource:
    def test_post_with_a_title(self, test_app_client, logged_in_rdu_user, db_session):

        measure_version = MeasureVersionFactory.create(data_sources=[])

        response = test_app_client.post(
            "/cms/data-sources", data={"measure_version_id": measure_version.id, "title": "Test"}
        )

        assert response.status_code == 302

        redirected_to_location = response.headers["Location"]

        match = re.search(r"/cms/data-sources/(\d+)$", redirected_to_location)

        assert match, f"Expected {redirected_to_location} to match /cms/data-sources/(\\d+)"

        data_source_id = match.group(1)

        data_source = DataSource.query.get(data_source_id)

        assert data_source, f"Expected to be able to find a data source with id {data_source_id}"
        assert data_source.title == "Test"

        measure_version = MeasureVersion.query.get(measure_version.id)

        assert measure_version.data_sources == [
            data_source
        ], "Expected data source to have been associated with the measure version"

    def test_post_with_no_title(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        response = test_app_client.post(
            "/cms/data-sources", data={"measure_version_id": measure_version.id, "title": ""}
        )
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Add data source" == page.find("title").text

    def test_post_with_no_measure_version_id(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.post("/cms/data-sources", data={"title": "Test"})

        assert response.status_code == 400

    def test_post_with_invalid_measure_version_id(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.post("/cms/data-sources", data={"measure_version_id": "999999999", "title": "Test"})

        assert response.status_code == 400


class TestEditDataSourceView:
    def __get_page(self, test_app_client, data_source):

        response = test_app_client.get(f"/cms/data-sources/{data_source.id}")

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def test_returns_200(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create()

        response, _ = self.__get_page(test_app_client, data_source)
        assert response.status_code == 200

    def test_page_title(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create()

        response, page = self.__get_page(test_app_client, data_source)
        assert "Edit data source" == page.find("h1").text
        assert "Edit data source" == page.find("title").text

    def test_edit_form(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police statistics 2019")

        response, page = self.__get_page(test_app_client, data_source)

        title_input = find_input_for_label_with_text(page, "Title of data source")

        assert "Police statistics 2019" == title_input["value"]


class TestUpdateDataSource:
    def test_post_with_an_updated_title(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")

        response = test_app_client.post(f"/cms/data-sources/{data_source.id}", data={"title": "Police statistics 2019"})

        assert response.status_code == 302

        redirected_to_location = response.headers["Location"]
        match = re.search(f"/cms/data-sources/{data_source.id}$", redirected_to_location)
        assert match, f"Expected {redirected_to_location} to match /cms/data-sources/{data_source.id}"

        # Re-fetch the model from the database to be sure that it has been saved.
        data_source = DataSource.query.get(data_source.id)

        assert data_source.title == "Police statistics 2019", "Expected title to have been updated"

    def test_post_with_no_title(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")

        response = test_app_client.post(f"/cms/data-sources/{data_source.id}", data={"title": ""})

        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Edit data source" == page.find("title").text

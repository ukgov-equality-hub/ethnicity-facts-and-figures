from bs4 import BeautifulSoup

from tests.models import DataSourceFactory

from tests.utils import find_input_for_label_with_text


class TestAddDataSourceView:
    def __get_page(self, test_app_client):

        response = test_app_client.get("/data-sources/new")

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def test_returns_200(self, test_app_client):

        response, _ = self.__get_page(test_app_client)
        assert response.status_code == 200

    def test_page_title(self, test_app_client):

        response, page = self.__get_page(test_app_client)
        assert "Add data source" == page.find("h1").text
        assert "Add data source" == page.find("title").text


class TestCreateDataSource:
    def test_post_with_a_title(self, test_app_client):

        response = test_app_client.post("/data-sources/new", data={"title": "Test"})

        assert response.status_code == 302
        assert response.headers["Location"] == "/data-sources/1"

    def test_post_with_no_title(self, test_app_client):

        response = test_app_client.post("/data-sources/new", data={"title": ""})
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Add data source" == page.find("title").text


class TestEditDataSourceView:
    def __get_page(self, test_app_client, data_source):

        response = test_app_client.get(f"/data-sources/{data_source.id}")

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def test_returns_200(self, test_app_client):

        data_source = DataSourceFactory.create()

        response, _ = self.__get_page(test_app_client, data_source)
        assert response.status_code == 200

    def test_page_title(self, test_app_client):

        data_source = DataSourceFactory.create()

        response, page = self.__get_page(test_app_client, data_source)
        assert "Edit data source" == page.find("h1").text
        assert "Edit data source" == page.find("title").text

    def test_edit_form(self, test_app_client):

        data_source = DataSourceFactory.create(title="Police statistics 2019")

        response, page = self.__get_page(test_app_client, data_source)

        title_input = find_input_for_label_with_text(page, "Title")

        assert "Police statistics 2019" == title_input["value"]


class TestUpdateDataSource:
    def test_post_with_an_updated_title(self, test_app_client):

        data_source = DataSourceFactory.create(title="Police stats 2019")

        response = test_app_client.post(f"/data-sources/{data_source.id}", data={"title": "Police statistics 2019"})

        assert response.status_code == 302
        assert response.headers["Location"] == "/data-sources/1"

    def test_post_with_no_title(self, test_app_client):

        data_source = DataSourceFactory.create(title="Police stats 2019")

        response = test_app_client.post(f"/data-sources/{data_source.id}", data={"title": ""})

        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Edit data source" == page.find("title").text

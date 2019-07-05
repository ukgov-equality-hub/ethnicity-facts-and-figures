from bs4 import BeautifulSoup

import re

from application.cms.models import DataSource, MeasureVersion

from tests.models import (
    DataSourceFactory,
    MeasureVersionFactory,
    TypeOfStatisticFactory,
    FrequencyOfReleaseFactory,
    OrganisationFactory,
)

from tests.utils import find_input_for_label_with_text


class TestAddDataSourceView:
    def __get_page(self, url, test_app_client):

        response = test_app_client.get(url)

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def __measure_edit_url(self, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit"

    def test_returns_200(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        url = f"{self.__measure_edit_url(measure_version)}/data-sources/new"

        response, _ = self.__get_page(url, test_app_client)
        assert response.status_code == 200

    def test_page_title(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        url = f"{self.__measure_edit_url(measure_version)}/data-sources/new"

        response, page = self.__get_page(url, test_app_client)
        assert "Add data source" == page.find("h1").text
        assert "Add data source" == page.find("title").text

    def test_returns_404_if_measure_doesnt_exist(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.get("/cms/topic/subtopic/measure/1.0/edit/data-sources/new")
        assert response.status_code == 404

    def test_returns_403_if_dept_user_cant_access_measure(self, test_app_client, logged_in_dept_user):

        measure_version = MeasureVersionFactory.create()

        url = f"{self.__measure_edit_url(measure_version)}/data-sources/new"

        response = test_app_client.get(url)
        assert response.status_code == 403

    def test_returns_200_if_dept_user_has_access_to_measure(self, test_app_client, logged_in_dept_user):

        measure_version = MeasureVersionFactory.create(measure__shared_with=[logged_in_dept_user])

        url = f"{self.__measure_edit_url(measure_version)}/data-sources/new"

        response = test_app_client.get(url)
        assert response.status_code == 200


class TestCreateDataSource:
    def __edit_measure_version_url(self, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit"

    def __create_data_source_for_measure_url(self, measure_version):

        edit_measure_url = self.__edit_measure_version_url(measure_version)

        return f"{edit_measure_url}/data-sources"

    def test_post_with_a_title_redirects_to_edit_measure(self, test_app_client, logged_in_rdu_user, db_session):

        type_of_statistic = TypeOfStatisticFactory.create()
        organisation = OrganisationFactory.create()
        frequency_of_release = FrequencyOfReleaseFactory.create()

        measure_version = MeasureVersionFactory.create(data_sources=[])
        url = self.__create_data_source_for_measure_url(measure_version)

        response = test_app_client.post(
            url,
            data={
                "measure_version_id": measure_version.id,
                "title": "Test",
                "type_of_data": "ADMINISTRATIVE",
                "type_of_statistic_id": type_of_statistic.id,
                "publisher_id": organisation.id,
                "source_url": "https://www.gov.uk/statistics/testing",
                "frequency_of_release_id": frequency_of_release.id,
                "purpose": "Testing",
            },
        )

        assert response.status_code == 302

        redirected_to_location = response.headers["Location"]

        edit_measure_url = self.__edit_measure_version_url(measure_version)

        match = re.search(f"{edit_measure_url}/data-sources/\\d+$", redirected_to_location)

        assert match, f"Expected {redirected_to_location} to match {edit_measure_url}/data-sources/\\d+"

        # Refresh measure version from database
        measure_version = MeasureVersion.query.get(measure_version.id)

        assert len(measure_version.data_sources) == 1, "Expected to be able to find a data source attached to measure"

        assert measure_version.data_sources[0].title == "Test", "Expected data source to have a Title set"

        measure_version = MeasureVersion.query.get(measure_version.id)

    def test_post_with_no_title(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory.create()

        url = self.__create_data_source_for_measure_url(measure_version)

        response = test_app_client.post(url, data={"measure_version_id": measure_version.id, "title": ""})
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Add data source" == page.find("title").text

    def test_post_with_invalid_measure_version_path_id(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.post("/cms/topic/subtopic/measure_slug/1.0/data-sources", data={"title": "Test"})

        assert response.status_code == 404

    def test_returns_403_if_dept_user_cant_access_measure(self, test_app_client, logged_in_dept_user):

        measure_version = MeasureVersionFactory.create(measure__shared_with=[])

        url = self.__create_data_source_for_measure_url(measure_version)

        response = test_app_client.post(url, data={"title": "Test"})

        assert response.status_code == 403

    def test_returns_200_if_dept_user_has_access_to_measure(self, test_app_client, logged_in_dept_user):

        measure_version = MeasureVersionFactory.create(measure__shared_with=[logged_in_dept_user])

        type_of_statistic = TypeOfStatisticFactory.create()
        organisation = OrganisationFactory.create()
        frequency_of_release = FrequencyOfReleaseFactory.create()

        url = self.__create_data_source_for_measure_url(measure_version)

        response = test_app_client.post(
            url,
            data={
                "measure_version_id": measure_version.id,
                "title": "Test",
                "type_of_data": "ADMINISTRATIVE",
                "type_of_statistic_id": type_of_statistic.id,
                "publisher_id": organisation.id,
                "source_url": "https://www.gov.uk/statistics/testing",
                "frequency_of_release_id": frequency_of_release.id,
                "purpose": "Testing",
            },
        )

        assert response.status_code == 302


class TestEditDataSourceView:
    def __get_page(self, test_app_client, data_source, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        url = f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit/data-sources/{data_source.id}"  # noqa: E501 (line too long)

        response = test_app_client.get(url)

        return (response, BeautifulSoup(response.data.decode("utf-8"), "html.parser"))

    def test_returns_200(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create()
        measure_version = MeasureVersionFactory.create(data_sources=[data_source])

        response, _ = self.__get_page(test_app_client, data_source, measure_version)
        assert response.status_code == 200

    def test_page_title_is_set(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create()
        measure_version = MeasureVersionFactory.create(data_sources=[data_source])

        response, page = self.__get_page(test_app_client, data_source, measure_version)
        assert "Edit data source" == page.find("h1").text
        assert "Edit data source" == page.find("title").text

    def test_edit_form_fields_populate_from_existing_data(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police statistics 2019")
        measure_version = MeasureVersionFactory.create(data_sources=[data_source])

        response, page = self.__get_page(test_app_client, data_source, measure_version)

        title_input = find_input_for_label_with_text(page, "Title of data source")

        assert "Police statistics 2019" == title_input["value"]

    def test_edit_page_if_data_source_not_associated_with_measure_version(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police statistics 2019")
        measure_version = MeasureVersionFactory.create(data_sources=[])

        response, _ = self.__get_page(test_app_client, data_source, measure_version)

        assert response.status_code == 404

    def test_edit_page_if_dept_user_cannot_access_measure(self, test_app_client, logged_in_dept_user):

        data_source = DataSourceFactory.create()
        measure_version = MeasureVersionFactory.create(data_sources=[data_source], measure__shared_with=[])

        response, _ = self.__get_page(test_app_client, data_source, measure_version)
        assert response.status_code == 403

    def test_edit_page_if_dept_user_has_access_to_measure(self, test_app_client, logged_in_dept_user):

        data_source = DataSourceFactory.create()
        measure_version = MeasureVersionFactory.create(
            data_sources=[data_source], measure__shared_with=[logged_in_dept_user]
        )

        response, _ = self.__get_page(test_app_client, data_source, measure_version)
        assert response.status_code == 200


class TestUpdateDataSource:
    def __update_data_source_url(self, data_source, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return (
            f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}"
            f"/edit/data-sources/{data_source.id}"
        )

    def __edit_measure_url(self, measure_version):

        measure_slug = measure_version.measure.slug
        subtopic_slug = measure_version.measure.subtopic.slug
        topic_slug = measure_version.measure.subtopic.topic.slug

        return f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/{measure_version.version}/edit"

    def test_post_with_an_updated_title_redirects_back_edit_data_source(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")
        measure_version = MeasureVersionFactory.create(data_sources=[data_source])

        url = self.__update_data_source_url(data_source, measure_version)

        response = test_app_client.post(
            url,
            data={
                "title": "Police statistics 2019",
                "type_of_data": "ADMINISTRATIVE",
                "type_of_statistic_id": data_source.type_of_statistic_id,
                "publisher_id": data_source.publisher_id,
                "source_url": data_source.source_url,
                "frequency_of_release_id": data_source.frequency_of_release_id,
                "purpose": data_source.purpose,
            },
        )

        # assert response.data.decode("utf-8") == ""
        assert response.status_code == 302

        redirected_to_location = response.headers["Location"]

        match = re.search(f"{url}$", redirected_to_location)

        assert match, f"Expected {redirected_to_location} to match {url}"

        # Re-fetch the model from the database to be sure that it has been saved.
        data_source = DataSource.query.get(data_source.id)

        assert data_source.title == "Police statistics 2019", "Expected title to have been updated"

    def test_post_with_no_title_redisplays_form_with_error(self, test_app_client, logged_in_rdu_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")
        measure_version = MeasureVersionFactory.create(data_sources=[data_source])

        url = self.__update_data_source_url(data_source, measure_version)
        response = test_app_client.post(url, data={"title": ""})

        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Error: Edit data source" == page.find("title").text

    def test_post_when_dept_user_cannot_access_measure(self, test_app_client, logged_in_dept_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")
        measure_version = MeasureVersionFactory.create(data_sources=[data_source], measure__shared_with=[])

        url = self.__update_data_source_url(data_source, measure_version)

        response = test_app_client.post(url, data={"title": "Police statistics 2019"})

        assert response.status_code == 403

    def test_post_when_dept_user_has_access_to_measure(self, test_app_client, logged_in_dept_user):

        data_source = DataSourceFactory.create(title="Police stats 2019")
        measure_version = MeasureVersionFactory.create(
            data_sources=[data_source], measure__shared_with=[logged_in_dept_user]
        )

        url = self.__update_data_source_url(data_source, measure_version)

        response = test_app_client.post(
            url,
            data={
                "title": "Police statistics 2019",
                "type_of_data": "ADMINISTRATIVE",
                "type_of_statistic_id": data_source.type_of_statistic_id,
                "publisher_id": data_source.publisher_id,
                "source_url": data_source.source_url,
                "frequency_of_release_id": data_source.frequency_of_release_id,
                "purpose": data_source.purpose,
            },
        )
        assert response.status_code == 302

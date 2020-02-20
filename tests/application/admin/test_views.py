from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import User, TypeOfUser
from application.cms.models import publish_status

from application.utils import generate_token

from tests.models import UserFactory, MeasureVersionFactory, DataSourceFactory, OrganisationFactory

from tests.utils import find_input_for_label_with_text

from werkzeug import ImmutableMultiDict


def test_standard_user_cannot_view_admin_urls(test_app_client, logged_in_rdu_user):
    resp = test_app_client.get(url_for("admin.index"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.users"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.user_by_id", user_id=logged_in_rdu_user.id), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.add_user"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.deactivate_user", user_id=logged_in_rdu_user.id), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.site_build"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403


def test_admin_user_can_view_admin_page(test_app_client, logged_in_admin_user):
    resp = test_app_client.get(url_for("admin.index"), follow_redirects=True)

    assert resp.status_code == 200


def test_admin_user_can_setup_account_for_rdu_user(
    app, test_app_client, logged_in_admin_user, mock_create_and_send_activation_email
):
    user_details = {"email": "invited_user@somedept.gov.uk", "user_type": TypeOfUser.RDU_USER.name}

    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    mock_create_and_send_activation_email.assert_called_once_with("invited_user@somedept.gov.uk", app)

    assert resp.status_code == 200

    user = User.query.filter_by(email="invited_user@somedept.gov.uk").one()
    assert user.active is False
    assert user.password is None
    assert user.confirmed_at is None

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Users"


def test_admin_user_can_setup_account_for_nhs_user(
    app, test_app_client, logged_in_admin_user, mock_create_and_send_activation_email
):
    user_details = {"email": "invited_user@nhs.net", "user_type": TypeOfUser.DEPT_USER.name}

    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    mock_create_and_send_activation_email.assert_called_once_with("invited_user@nhs.net", app)

    assert resp.status_code == 200

    user = User.query.filter_by(email="invited_user@nhs.net").one()
    assert user.active is False
    assert user.password is None
    assert user.confirmed_at is None

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Users"


def test_admin_user_cannot_setup_account_for_user_with_non_gov_uk_email(test_app_client, logged_in_admin_user):
    user_details = {"email": "invited_user@notgovemail.com", "user_type": "INTERNAL_USER"}
    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert "Enter a government email address" in page.find("div", class_="govuk-error-summary").text
    assert not User.query.filter_by(email="invited_user@notgovemail.com").first()

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Error: Add user"


def test_admin_user_can_deactivate_user_account(test_app_client, logged_in_admin_user):
    user = UserFactory(active=True, user_type=TypeOfUser.RDU_USER)
    assert user.active is True

    resp = test_app_client.get(url_for("admin.deactivate_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == f"User account for: {user.email} deactivated"
    )
    assert user.active is False


def test_admin_user_can_grant_or_remove_rdu_user_admin_rights(test_app_client, logged_in_admin_user):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)
    assert not rdu_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == "User %s is now an admin user" % rdu_user.email
    )

    assert rdu_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == "User %s is now a standard RDU user" % rdu_user.email
    )

    assert rdu_user.is_rdu_user()


def test_admin_user_cannot_grant_departmental_user_admin_rights(test_app_client, logged_in_admin_user):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    assert not dept_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=dept_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="eff-flash-message__body").get_text(strip=True) == "Only RDU users can be made admin"

    assert not dept_user.is_admin_user()


def test_admin_user_cannot_remove_their_own_admin_rights(test_app_client, logged_in_admin_user):
    assert logged_in_admin_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=logged_in_admin_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == "You can't remove your own admin rights"
    )

    assert logged_in_admin_user.is_admin_user()


def test_admin_user_cannot_add_user_if_case_insensitive_email_in_use(test_app_client, logged_in_admin_user):
    existing_rdu_user = UserFactory(email="existing@rdu.gov.uk", user_type=TypeOfUser.RDU_USER)
    user_details = {"email": existing_rdu_user.email.upper(), "user_type": TypeOfUser.RDU_USER.name}

    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").text.strip()
        == f"User: {existing_rdu_user.email} is already in the system"
    )


def test_reset_password_rejects_easy_password(app, test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)

    token = generate_token(rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "long-enough-but-too-easy", "confirm_password": "long-enough-but-too-easy"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").text.strip()
        == """Your password is too weak. It has to be at least 10 characters long and use a mix of numbers, special
                characters as well as upper and lowercase letters. Avoid using common patterns and repeated characters.
                """
    )


def test_reset_password_accepts_good_password(app, test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)

    token = generate_token(rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "This sh0uld b3 Ok n0w", "confirm_password": "This sh0uld b3 Ok n0w"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("h1").text.strip() == "Password updated"


def test_measure_versions_in_all_states_are_available_to_share(test_app_client, logged_in_admin_user):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    num_measures = len(publish_status.keys())
    for status in publish_status.keys():
        MeasureVersionFactory(status=status)

    resp = test_app_client.get(url_for("admin.user_by_id", user_id=dept_user.id), follow_redirects=True)
    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html." "parser")
    select = page.find("select", {"id": "measure-picker"})

    # There should be an option for "select a measure", plus one for each actual measure.
    assert len(select.findAll("option")) == num_measures + 1


def test_admin_user_can_share_page_with_dept_user(test_app_client):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER)

    measure_version = MeasureVersionFactory(status="DRAFT")
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    # dept user can't get to page
    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 403

    # admin user shares page
    with test_app_client.session_transaction() as session:
        session["user_id"] = admin_user.id

    data = {"measure-picker": measure_version.id}

    resp = test_app_client.post(
        url_for("admin.share_page_with_user", user_id=dept_user.id), data=data, follow_redirects=True
    )
    assert measure_version.measure.shared_with == [dept_user]
    assert resp.status_code == 200

    # dept user can view or edit page
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200


def test_admin_user_can_remove_share_of_page_with_dept_user(test_app_client):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER)

    measure_version = MeasureVersionFactory(status="DRAFT", measure__shared_with=[dept_user])

    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 200

    # admin user removes share
    with test_app_client.session_transaction() as session:
        session["user_id"] = admin_user.id

    resp = test_app_client.get(
        url_for("admin.remove_shared_page_from_user", measure_id=measure_version.measure_id, user_id=dept_user.id),
        follow_redirects=True,
    )

    assert resp.status_code == 200

    # dept user can no longer access page
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert resp.status_code == 403


def test_admin_user_can_delete_non_admin_user_account(test_app_client, logged_in_admin_user):
    user = UserFactory(email="someuser@somedept.gov.uk", active=True, user_type=TypeOfUser.RDU_USER)

    assert user.active

    resp = test_app_client.get(url_for("admin.delete_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == "User account for: someuser@somedept.gov.uk deleted"
    )

    assert User.query.filter_by(email="someuser@somedept.gov.uk").first() is None


class TestDataSourcesView:
    @property
    def __path(self):
        return url_for("admin.data_sources")

    def __path_with_query(self, query):
        return url_for("admin.data_sources", q=query)

    def test_department_user_cannot_see_page(self, test_app_client, logged_in_dept_user):

        response = test_app_client.get(self.__path)
        assert response.status_code == 403

    def test_rdu_user_cannot_see_page(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.get(self.__path)
        assert response.status_code == 403

    def test_admin_user_can_see_all_data_sources(self, test_app_client, logged_in_admin_user):

        DataSourceFactory.create(title="Police statistics 2019")
        DataSourceFactory.create(title="2011 Census of England and Wales")

        response = test_app_client.get(self.__path)
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Data sources" == page.find("h1").text
        assert "Data sources" == page.find("title").text

        assert "Police statistics 2019" in page.find("main").text
        assert "2011 Census of England and Wales" in page.find("main").text

    def test_admin_user_search_for_data_sources(self, test_app_client, logged_in_admin_user):

        DataSourceFactory.create(title="Police statistics 2019")
        DataSourceFactory.create(title="2011 Census of England and Wales")

        response = test_app_client.get(self.__path_with_query("police"))
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert response.status_code == 200
        assert "Data sources" == page.find("h1").text
        assert "police - Search data sources" == page.find("title").text

        assert "Police statistics 2019" in page.find("main").text
        assert "2011 Census of England and Wales" not in page.find("main").text

        input_field = find_input_for_label_with_text(page, "Search data sources")
        assert input_field["value"] == "police"

    def test_data_sources_ordered_lexicographically_by_title(self, test_app_client, logged_in_admin_user):
        DataSourceFactory.create(title="Police statistics 2019")
        DataSourceFactory.create(title="2011 Census of England and Wales")

        response = test_app_client.get(self.__path)
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        main = page.find("main")
        assert main.text.index("2011 Census of England and Wales") < main.text.index("Police statistics 2019")

    def test_form_has_checkbox_for_each_data_source(self, test_app_client, logged_in_admin_user):
        ds1 = DataSourceFactory.create(title="Police statistics 2019")
        ds2 = DataSourceFactory.create(title="2011 Census of England and Wales")

        response = test_app_client.get(self.__path)
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        form = page.find("form", action=url_for("admin.merge_data_sources"))
        assert form

        assert find_input_for_label_with_text(form, "Police statistics 2019").get("value") == str(ds1.id)
        assert find_input_for_label_with_text(form, "2011 Census of England and Wales").get("value") == str(ds2.id)


class TestMergeDataSourcesView:
    @property
    def __path(self):
        return url_for("admin.merge_data_sources")

    @staticmethod
    def __path_with_data_source_ids(data_source_ids):
        return url_for("admin.merge_data_sources", data_sources=data_source_ids)

    def test_rdu_user_cannot_see_data_source_merge(self, test_app_client, logged_in_rdu_user):

        response = test_app_client.get(self.__path)

        assert response.status_code == 403

    def test_admin_user_viewing_two_data_source_to_merge(self, test_app_client, logged_in_admin_user):

        organisation = OrganisationFactory.create(name="Home Office")

        data_source_1 = DataSourceFactory.create(
            title="2019 police statistics",
            source_url="https://www.gov.uk/statistics/police/2019",
            publisher=organisation,
        )
        data_source_2 = DataSourceFactory.create(
            title="Police statistics 2019", source_url="https://statistics.gov.uk/police/2019", publisher=organisation
        )

        response = test_app_client.get(self.__path_with_data_source_ids([data_source_1.id, data_source_2.id]))

        assert response.status_code == 200

        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

        assert "Merge 2 data sources" == page.find("h1").text
        assert "Merge 2 data sources" == page.find("title").text

        assert "2019 police statistics" in page.text
        assert "Police statistics 2019" in page.text

    def test_admin_user_attempting_to_merge_non_existent_ids(self, test_app_client, logged_in_admin_user):

        organisation = OrganisationFactory.create(name="Home Office")

        data_source_1 = DataSourceFactory.create(
            title="2019 police statistics",
            source_url="https://www.gov.uk/statistics/police/2019",
            publisher=organisation,
        )

        response = test_app_client.get(self.__path_with_data_source_ids([data_source_1.id, 9999]))

        assert response.status_code == 400

    def test_merging_two_data_sources(self, test_app_client, logged_in_admin_user):

        DataSourceFactory.create()

        data_source_1 = DataSourceFactory.create(title="Police Statistics 2019")
        data_source_2 = DataSourceFactory.create(title="Police Stats 2019")

        response = test_app_client.post(
            self.__path_with_data_source_ids(data_source_ids=[data_source_1.id, data_source_2.id]),
            data=ImmutableMultiDict((("ids", data_source_1.id), ("ids", data_source_2.id), ("keep", data_source_1.id))),
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.location == url_for("admin.data_sources", _external=True)

        # Now follow the redirect
        response_2 = test_app_client.get(response.location)

        assert response_2.status_code == 200
        page = BeautifulSoup(response_2.data.decode("utf-8"), "html.parser")

        assert "Police Statistics 2019" in page.find("main").text
        assert "Police Stats 2019" not in page.find("main").text

    def test_failing_to_select_one_to_keep(self, test_app_client, logged_in_admin_user):

        DataSourceFactory.create()

        data_source_1 = DataSourceFactory.create(title="Police Statistics 2019")
        data_source_2 = DataSourceFactory.create(title="Police Stats 2019")

        response = test_app_client.post(
            self.__path_with_data_source_ids(data_source_ids=[data_source_1.id, data_source_2.id]),
            data=ImmutableMultiDict((("ids", data_source_1.id), ("ids", data_source_2.id))),
            follow_redirects=False,
        )

        assert response.status_code == 200

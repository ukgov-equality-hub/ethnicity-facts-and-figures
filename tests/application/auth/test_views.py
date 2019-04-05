import pytest

from flask import url_for
from bs4 import BeautifulSoup

from application.auth.models import TypeOfUser
from tests.models import UserFactory
from tests.utils import page_displays_error_matching_message


@pytest.mark.parametrize(
    "cms_url",
    (
        "/admin/",
        "/admin/users",
        "/admin/users/123",
        "/admin/users/123/share",
        "/admin/users/123/remove-share/345",
        "/admin/users/add",
        "/admin/users/123/resend-account-activation-email",
        "/admin/users/123/deactivate",
        "/admin/users/123/delete",
        "/admin/users/123/make-admin",
        "/admin/users/123/make-rdu-user",
        "/admin/site-build",
        "/cms/topic-name/subtopic-name/measure/new",
        "/cms/topic-name/subtopic-name/measure/2.0/uploads/upload/edit",
        "/cms/topic-name/subtopic-name/measure/2.0/edit",
        "/cms/topic-name/subtopic-name/measure/2.0/upload",
        "/cms/topic-name/subtopic-name/measure/2.0/dimension/new",
        "/cms/topic-name/subtopic-name/measure/2.0/dimension/edit",
        "/cms/topic-name/subtopic-name/measure/2.0/dimension/create-chart",
        "/cms/topic-name/subtopic-name/measure/2.0/dimension/create-table",
        "/cms/topic-name/subtopic-name/measure/versions",
        "/cms/topic-name/subtopic-name/measure/2.0/delete",
        "/cms/topic-name/subtopic-name/measure/2.0/new-version",
        "/dashboards/",
        "/dashboards/published",
        "/dashboards/measures",
        "/dashboards/planned-pages",
        "/dashboards/ethnic-groups",
        "/dashboards/ethnicity-classifications",
        "/dashboards/ethnicity-classifications/5",
        "/dashboards/geographic-breakdown",
        "/dashboards/geographic-breakdown/wales",
        "/topic/subtopic/measure/2.0/export",
        "/topic/subtopic/measure/2.0",
    ),
)
def test_logged_out_user_redirects_to_login(test_app_client, cms_url):
    resp = test_app_client.get(cms_url)

    assert resp.status_code == 302
    assert resp.location == url_for("security.login", next=cms_url, _external=True)


def test_unhashed_user_password_automatically_hashed_on_login_attempt(test_app_client):
    user = UserFactory(password="password123", active=True)
    assert user.password == "password123"

    test_app_client.post(
        url_for("security.login"), data={"email": user.email, "password": "password123"}, follow_redirects=True
    )

    assert user.password != "password123"


def test_successfully_logged_in_user_goes_to_main_page(test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, password="password123", active=True)

    resp = test_app_client.post(
        url_for("security.login"), data={"email": rdu_user.email, "password": rdu_user.password}, follow_redirects=True
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.string.strip() == "Ethnicity facts and figures"


def test_login_with_bad_credentials_shows_errors(test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, password="password123", active=True)

    # Wrong username
    response = test_app_client.post(
        url_for("security.login"),
        data={"email": "bad@email.address.gov.uk", "password": rdu_user.password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert page_displays_error_matching_message(response, "Check your email address")
    assert page_displays_error_matching_message(response, "Check your password")

    # Wrong password
    response = test_app_client.post(
        url_for("security.login"), data={"email": rdu_user.email, "password": "wrong-password"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert page_displays_error_matching_message(response, "Check your email address")
    assert page_displays_error_matching_message(response, "Check your password")


def test_unsuccessful_login_returns_to_login_page(test_app_client):

    resp = test_app_client.post(
        url_for("security.login"),
        data={"email": "notauser@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.h1.string.strip() == "Login"


def test_should_redirect_to_homepage_on_logout(test_app_client, logged_in_rdu_user):
    res = test_app_client.post("/auth/logout")
    assert res.status_code == 302
    assert res.location == url_for("static_site.index", _external=True)


def test_should_expire_session_vars_on_logout(test_app_client, logged_in_rdu_user):

    with test_app_client.session_transaction() as session:
        session["session_data"] = "Secret stuff"
        assert session.get("session_data") == "Secret stuff"

    test_app_client.post(url_for("auth.logout"))

    with test_app_client.session_transaction() as session:
        assert session.get("session_data") is None

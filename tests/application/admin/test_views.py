from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import User, TypeOfUser
from application.utils import generate_token

from tests.models import UserFactory, MeasureVersionFactory


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


def test_admin_user_cannot_setup_account_for_user_with_non_gov_uk_email(test_app_client, logged_in_admin_user):
    user_details = {"email": "invited_user@notgovemail.com", "user_type": "INTERNAL_USER"}
    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("span", class_="error-message").string == "Enter a government email address"
    assert not User.query.filter_by(email="invited_user@notgovemail.com").first()

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Error: Add user"


def test_admin_user_can_deactivate_user_account(test_app_client, logged_in_admin_user):
    user = UserFactory(active=True, user_type=TypeOfUser.RDU_USER)
    assert user.active is True

    resp = test_app_client.get(url_for("admin.deactivate_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == f"User account for: {user.email} deactivated"
    assert user.active is False


def test_admin_user_can_grant_or_remove_rdu_user_admin_rights(test_app_client, logged_in_admin_user):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)
    assert not rdu_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User %s is now an admin user" % rdu_user.email

    assert rdu_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User %s is now a standard RDU user" % rdu_user.email

    assert rdu_user.is_rdu_user()


def test_admin_user_cannot_grant_departmental_user_admin_rights(test_app_client, logged_in_admin_user):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    assert not dept_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=dept_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "Only RDU users can be made admin"

    assert not dept_user.is_admin_user()


def test_admin_user_cannot_remove_their_own_admin_rights(test_app_client, logged_in_admin_user):
    assert logged_in_admin_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=logged_in_admin_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "You can't remove your own admin rights"

    assert logged_in_admin_user.is_admin_user()


def test_admin_user_cannot_add_user_if_case_insensitive_email_in_use(test_app_client, logged_in_admin_user):
    existing_rdu_user = UserFactory(email="existing@rdu.gov.uk", user_type=TypeOfUser.RDU_USER)
    user_details = {"email": existing_rdu_user.email.upper(), "user_type": TypeOfUser.RDU_USER.name}

    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="alert-box").text.strip() == f"User: {existing_rdu_user.email} is already in the system"
    )


def test_reset_password_rejects_easy_password(app, test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)

    token = generate_token(rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "long-enough-but-too-easy", "confirm_password": "long-enough-but-too-easy"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="alert-box").text.strip()
        == "Your password is too weak. Use a mix of numbers as well as upper and lowercase letters"
    )


def test_reset_password_accepts_good_password(app, test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER)

    token = generate_token(rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "This sh0uld b3 Ok n0w", "confirm_password": "This sh0uld b3 Ok n0w"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("h1").text.strip() == "Password updated"


def test_admin_user_can_share_page_with_dept_user(test_app_client):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER)

    measure_page = MeasureVersionFactory(id=100)
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    # dept user can't get to page
    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 403

    # admin user shares page
    with test_app_client.session_transaction() as session:
        session["user_id"] = admin_user.id

    data = {"measure-picker": measure_page.id}

    resp = test_app_client.post(
        url_for("admin.share_page_with_user", user_id=dept_user.id), data=data, follow_redirects=True
    )
    assert measure_page.measure.shared_with == [dept_user]
    assert resp.status_code == 200

    # dept user can view or edit page
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 200

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 200


def test_admin_user_can_remove_share_of_page_with_dept_user(test_app_client):
    dept_user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER)

    measure_page = MeasureVersionFactory(measure__shared_with=[dept_user])

    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 200

    # admin user removes share
    with test_app_client.session_transaction() as session:
        session["user_id"] = admin_user.id

    resp = test_app_client.get(
        url_for("admin.remove_shared_page_from_user", measure_id=measure_page.measure_id, user_id=dept_user.id),
        follow_redirects=True,
    )

    assert resp.status_code == 200

    # dept user can no longer access page
    with test_app_client.session_transaction() as session:
        session["user_id"] = dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_page.measure.subtopic.topic.slug,
            subtopic_slug=measure_page.measure.subtopic.slug,
            measure_slug=measure_page.measure.slug,
            version=measure_page.version,
        )
    )

    assert resp.status_code == 403


def test_admin_user_can_delete_non_admin_user_account(test_app_client, logged_in_admin_user):
    user = UserFactory(email="someuser@somedept.gov.uk", active=True, user_type=TypeOfUser.RDU_USER)

    assert user.active

    resp = test_app_client.get(url_for("admin.delete_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User account for: someuser@somedept.gov.uk deleted"

    assert User.query.filter_by(email="someuser@somedept.gov.uk").first() is None

from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import User, TypeOfUser
from application.utils import generate_token


def test_standard_user_cannot_view_admin_urls(test_app_client, mock_rdu_user):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(url_for("admin.index"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.users"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.user_by_id", user_id=mock_rdu_user.id), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.add_user"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.deactivate_user", user_id=mock_rdu_user.id), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403

    resp = test_app_client.get(url_for("admin.site_build"), follow_redirects=True)

    assert resp.status == "403 FORBIDDEN"
    assert resp.status_code == 403


def test_admin_user_can_view_admin_page(test_app_client, mock_admin_user):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.index"), follow_redirects=True)

    assert resp.status_code == 200


def test_admin_user_can_setup_account_for_rdu_user(
    app, test_app_client, mock_admin_user, mock_create_and_send_activation_email
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    user_details = {"email": "invited_user@somedept.gov.uk", "user_type": TypeOfUser.RDU_USER.name}

    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    mock_create_and_send_activation_email.assert_called_once_with("invited_user@somedept.gov.uk", app)

    assert resp.status_code == 200

    user = User.query.filter_by(email="invited_user@somedept.gov.uk").one()
    assert not user.active
    assert not user.password
    assert not user.confirmed_at

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Users"


def test_admin_user_cannot_setup_account_for_user_with_non_gov_uk_email(test_app_client, mock_admin_user):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    user_details = {"email": "invited_user@notgovemail.com", "user_type": "INTERNAL_USER"}
    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("span", class_="error-message").string == "Enter a government email address"
    assert not User.query.filter_by(email="invited_user@notgovemail.com").first()

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Error: Add user"


def test_admin_user_can_deactivate_user_account(test_app_client, mock_admin_user, db, db_session):

    db.session.add(User(email="someuser@somedept.gov.uk", active=True, user_type=TypeOfUser.RDU_USER))
    db.session.commit()

    user = User.query.filter_by(email="someuser@somedept.gov.uk").one()
    assert user.active

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.deactivate_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User account for: someuser@somedept.gov.uk deactivated"

    user = User.query.filter_by(email="someuser@somedept.gov.uk").one()
    assert not user.active


def test_admin_user_can_grant_or_remove_rdu_user_admin_rights(test_app_client, mock_rdu_user, mock_admin_user):

    assert not mock_rdu_user.is_admin_user()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=mock_rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User %s is now an admin user" % mock_rdu_user.email

    assert mock_rdu_user.is_admin_user()

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=mock_rdu_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="alert-box").span.string == "User %s is now a standard RDU user" % mock_rdu_user.email
    )

    assert mock_rdu_user.is_rdu_user()


def test_admin_user_cannot_grant_departmental_user_admin_rights(test_app_client, mock_dept_user, mock_admin_user):

    assert not mock_dept_user.is_admin_user()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.make_admin_user", user_id=mock_dept_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "Only RDU users can be made admin"

    assert not mock_dept_user.is_admin_user()


def test_admin_user_cannot_remove_their_own_admin_rights(test_app_client, mock_admin_user):

    assert mock_admin_user.is_admin_user()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.make_rdu_user", user_id=mock_admin_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "You can't remove your own admin rights"

    assert mock_admin_user.is_admin_user()


def test_admin_user_cannot_add_user_if_case_insensitive_email_in_use(test_app_client, mock_admin_user, mock_rdu_user):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    user_details = {"email": mock_rdu_user.email.upper(), "user_type": TypeOfUser.RDU_USER.name}
    resp = test_app_client.post(url_for("admin.add_user"), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="alert-box").text.strip() == "User: %s is already in the system" % mock_rdu_user.email
    )


def test_reset_password_rejects_easy_password(app, test_app_client, mock_rdu_user):

    token = generate_token(mock_rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "long-enough-but-too-easy", "confirm_password": "long-enough-but-too-easy"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="alert-box").text.strip()
        == "Your password is too weak. Use a mix of numbers as well as upper and lowercase letters"
    )  # noqa


def test_reset_password_accepts_good_password(app, test_app_client, mock_rdu_user):

    token = generate_token(mock_rdu_user.email, app)
    confirmation_url = url_for("auth.reset_password", token=token, _external=True)

    user_details = {"password": "This sh0uld b3 Ok n0w", "confirm_password": "This sh0uld b3 Ok n0w"}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("h1").text.strip() == "Password updated"


def test_admin_user_can_share_page_with_dept_user(test_app_client, mock_dept_user, mock_admin_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    # dept user can't get to page
    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403

    # admin user shares page
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    data = {"measure-picker": stub_measure_page.guid}

    resp = test_app_client.post(
        url_for("admin.share_page_with_user", user_id=mock_dept_user.id), data=data, follow_redirects=True
    )

    assert resp.status_code == 200

    # dept user can view or edit page
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200


def test_admin_user_can_remove_share_of_page_with_dept_user(
    test_app_client, mock_dept_user, mock_admin_user, stub_measure_page, db_session
):

    stub_measure_page.shared_with.append(mock_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200

    # admin user removes share
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(
        url_for(
            "admin.remove_shared_page_from_user", measure_id=stub_measure_page.measure_id, user_id=mock_dept_user.id
        ),
        follow_redirects=True,
    )

    assert resp.status_code == 200

    # dept user can no longer access page
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403


def test_admin_user_can_delete_non_admin_user_account(test_app_client, mock_admin_user, db, db_session):

    db.session.add(User(email="someuser@somedept.gov.uk", active=True, user_type=TypeOfUser.RDU_USER))
    db.session.commit()

    user = User.query.filter_by(email="someuser@somedept.gov.uk").one()
    assert user.active

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    resp = test_app_client.get(url_for("admin.delete_user", user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "User account for: someuser@somedept.gov.uk deleted"

    assert User.query.filter_by(email="someuser@somedept.gov.uk").first() is None

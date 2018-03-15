from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import User
from application.utils import generate_token


def test_standard_user_cannot_view_admin_urls(test_app_client, mock_user):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('admin.index'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.users'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.user_by_id', user_id=mock_user.id), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.add_user'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.deactivate_user', user_id=mock_user.id), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.site_build'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403


def test_admin_user_can_view_admin_page(test_app_client, mock_admin_user):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.index'), follow_redirects=True)

    assert resp.status_code == 200


def test_admin_user_can_setup_account_for_internal_user(app,
                                                        test_app_client,
                                                        mock_admin_user,
                                                        mock_create_and_send_activation_email):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    user_details = {'email': 'invited_user@somedept.gov.uk', 'user_type': 'INTERNAL_USER'}

    resp = test_app_client.post(url_for('admin.add_user'), data=user_details, follow_redirects=True)

    mock_create_and_send_activation_email.assert_called_once_with('invited_user@somedept.gov.uk', app)

    assert resp.status_code == 200

    user = User.query.filter_by(email='invited_user@somedept.gov.uk').one()
    assert not user.active
    assert not user.password
    assert not user.confirmed_at


def test_admin_user_cannot_setup_account_for_user_with_non_gov_uk_email(test_app_client, mock_admin_user):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    user_details = {'email': 'invited_user@notgovemail.com', 'user_type': 'INTERNAL_USER'}
    resp = test_app_client.post(url_for('admin.add_user'), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('span', class_="error-message").string == 'Enter a government email address'
    assert not User.query.filter_by(email='invited_user@notgovemail.com').first()


def test_admin_user_can_deactivate_user_account(test_app_client, mock_admin_user, db, db_session):

    db.session.add(User(email='someuser@somedept.gov.uk', active=True))
    db.session.commit()

    user = User.query.filter_by(email='someuser@somedept.gov.uk').one()
    assert user.active

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.deactivate_user', user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'User account for: someuser@somedept.gov.uk deactivated'

    user = User.query.filter_by(email='someuser@somedept.gov.uk').one()
    assert not user.active


def test_admin_user_can_grant_or_remove_internal_user_admin_rights(test_app_client,
                                                                   mock_user,
                                                                   mock_admin_user):

    assert not mock_user.has_role('ADMIN')

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.give_user_admin_rights', user_id=mock_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Gave admin rights to %s' % mock_user.email

    assert mock_user.has_role('ADMIN')

    resp = test_app_client.get(url_for('admin.remove_user_admin_rights', user_id=mock_user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Removed admin rights from %s' % mock_user.email

    assert not mock_user.has_role('ADMIN')


def test_admin_user_cannot_grant_departmental_user_admin_rights(test_app_client, mock_dept_user, mock_admin_user):

    assert not mock_dept_user.has_role('ADMIN')

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.give_user_admin_rights',
                                       user_id=mock_dept_user.id),
                               follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'Only internal users can be give admin rights'

    assert not mock_dept_user.has_role('ADMIN')


def test_admin_user_cannot_remove_their_own_admin_rights(test_app_client, mock_admin_user):

    assert mock_admin_user.has_role('ADMIN')

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.remove_user_admin_rights',
                                       user_id=mock_admin_user.id),
                               follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == "You can't remove your own admin rights"

    assert mock_admin_user.has_role('ADMIN')


def test_admin_user_cannot_add_user_if_case_insensitive_email_in_use(test_app_client, mock_admin_user, mock_user):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    user_details = {'email': mock_user.email.upper(), 'user_type': 'INTERNAL_USER'}
    resp = test_app_client.post(url_for('admin.add_user'), data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").text.strip() == 'User: %s is already in the system' % mock_user.email


def test_reset_password_rejects_easy_password(app, test_app_client, mock_user):

    token = generate_token(mock_user.email, app)
    confirmation_url = url_for('auth.reset_password', token=token, _external=True)

    user_details = {'password': 'long-enough-but-too-easy', 'confirm_password': 'long-enough-but-too-easy'}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").text.strip() == 'Your password is too weak. Use a mix of numbers as well as upper and lowercase letters'  # noqa


def test_reset_password_accepts_good_password(app, test_app_client, mock_user):

    token = generate_token(mock_user.email, app)
    confirmation_url = url_for('auth.reset_password', token=token, _external=True)

    user_details = {'password': 'This sh0uld b3 Ok n0w', 'confirm_password': 'This sh0uld b3 Ok n0w'}
    resp = test_app_client.post(confirmation_url, data=user_details)

    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('h1').text.strip() == 'Password updated'

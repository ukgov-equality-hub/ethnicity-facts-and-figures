from unittest.mock import ANY

from bs4 import BeautifulSoup
from flask import url_for, render_template, current_app

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


def test_admin_user_can_setup_account_for_internal_user(app, test_app_client, mock_admin_user, mock_send_email):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    user_details = {'email': 'invited_user@somewhere.com', 'user_type': 'INTERNAL_USER'}

    resp = test_app_client.post(url_for('admin.add_user'), data=user_details, follow_redirects=True)

    token = generate_token('invited_user@somewhere.com', current_app)
    confirmation_url = url_for('register.confirm_account',
                               token=token,
                               _external=True)

    expected_message = render_template('admin/confirm_account.html',
                                       confirmation_url=confirmation_url,
                                       user=mock_admin_user)

    mock_send_email.assert_called_once_with(app.config['RDU_EMAIL'], 'invited_user@somewhere.com', ANY)

    assert resp.status_code == 200

    user = User.query.filter_by(email='invited_user@somewhere.com').one()
    assert not user.active
    assert not user.password
    assert not user.confirmed_at


def test_admin_user_can_deactivate_user_account(test_app_client, mock_admin_user, db, db_session):

    db.session.add(User(email='someuser@somemail.com', active=True))
    db.session.commit()

    user = User.query.filter_by(email='someuser@somemail.com').one()
    assert user.active

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    resp = test_app_client.get(url_for('admin.deactivate_user', user_id=user.id), follow_redirects=True)

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('div', class_="alert-box").span.string == 'User account for: someuser@somemail.com deactivated'

    user = User.query.filter_by(email='someuser@somemail.com').one()
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

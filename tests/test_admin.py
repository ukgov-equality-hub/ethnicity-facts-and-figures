from bs4 import BeautifulSoup
from flask import url_for, render_template, current_app

from application.auth.models import User
from application.utils import _generate_token


def test_standard_user_cannot_view_admin_urls(test_app_client, mock_user):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    resp = test_app_client.get(url_for('admin.index'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.users'), follow_redirects=True)

    assert resp.status == '403 FORBIDDEN'
    assert resp.status_code == 403

    resp = test_app_client.get(url_for('admin.user', user_id=mock_user.id), follow_redirects=True)

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


def test_admin_user_can_setup_account_for_internal_user(test_app_client, mock_admin_user, mock_send_email, db_session):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_admin_user.id

    user_details = {'email': 'invited_user@somewhere.com', 'user_type': 'INTERNAL_USER'}

    resp = test_app_client.post(url_for('admin.add_user'), data=user_details, follow_redirects=True)

    token = _generate_token('invited_user@somewhere.com', current_app)
    confirmation_url = url_for('register.confirm_account',
                               token=token,
                               _external=True)

    expected_message = render_template('admin/confirm_account.html',
                                       confirmation_url=confirmation_url,
                                       user=mock_admin_user)

    mock_send_email.assert_called_once_with('invited_user@somewhere.com', expected_message)

    assert resp.status_code == 200

    user = User.query.filter_by(email='invited_user@somewhere.com').one()
    assert not user.active
    assert not user.password
    assert not user.confirmed_at


def test_admin_user_can_deactivate_user_account(mocker, test_app_client, mock_admin_user, db, db_session):

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

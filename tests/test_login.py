from flask import url_for


def test_logged_out_user_redirects_to_login(app):
    resp = app.get('/')

    assert resp.status_code == 302
    assert resp.location == url_for('auth.login', next='/')


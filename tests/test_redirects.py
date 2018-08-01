from flask import url_for

from manage import add_redirect_rule


def test_redirects_(test_app_client, mock_user, db_session):
    # GIVEN a fresh database
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    # WHEN we add a redirect
    from_uri = 'fish'
    to_uri = 'chips'
    add_redirect_rule(from_uri=from_uri, to_uri=to_uri)

    # THEN output contains redirect from_uri and to_uri
    resp = test_app_client.get(url_for('redirects.index'))
    assert resp.status_code == 200
    xml_string = str(resp.data)
    assert '<KeyPrefixEquals>%s</KeyPrefixEquals' % from_uri in xml_string
    assert '<ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith' % to_uri in xml_string

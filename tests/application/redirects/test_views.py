from flask import url_for

from manage import add_redirect_rule, delete_redirect_rule


def test_create_redirect(test_app_client, mock_rdu_user, db_session):
    # GIVEN a fresh database
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    # WHEN we add a redirect
    from_uri = "fish"
    to_uri = "chips"
    add_redirect_rule(from_uri=from_uri, to_uri=to_uri)

    # THEN output contains redirect from_uri and to_uri
    resp = test_app_client.get(url_for("redirects.index"))
    assert resp.status_code == 200
    xml_string = str(resp.data)
    assert "<KeyPrefixEquals>%s</KeyPrefixEquals" % from_uri in xml_string
    assert "<ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith" % to_uri in xml_string


def test_delete_redirect(test_app_client, mock_rdu_user, db_session):
    # GIVEN a database with redirects in it
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id
    add_redirect_rule(from_uri="alabama", to_uri="alaska")
    add_redirect_rule(from_uri="michigan", to_uri="maine")

    # WHEN we delete a redirect
    delete_redirect_rule(from_uri="alabama")

    # THEN output does not contain redirect alamaba and alaska
    resp = test_app_client.get(url_for("redirects.index"))
    assert resp.status_code == 200
    xml_string = str(resp.data)

    assert "<KeyPrefixEquals>%s</KeyPrefixEquals" % "alabama" not in xml_string
    assert "<ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith" % "alaska" not in xml_string

    # AND output does contain redirect michigan to main
    assert "<KeyPrefixEquals>%s</KeyPrefixEquals" % "michigan" in xml_string
    assert "<ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith" % "maine" in xml_string

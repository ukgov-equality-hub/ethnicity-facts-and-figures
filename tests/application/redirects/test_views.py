from flask import url_for

from manage import add_redirect_rule, delete_redirect_rule
from flaky import flaky


@flaky(max_runs=10, min_passes=1)
def test_create_redirect(test_app_client, logged_in_rdu_user):
    # GIVEN a fresh database
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


@flaky(max_runs=10, min_passes=1)
def test_delete_redirect(test_app_client, logged_in_rdu_user):
    # GIVEN a database with redirects in it
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


@flaky(max_runs=10, min_passes=1)
def test_redirect_ordering_sorts_by_most_path_fragments_then_alphabetical(test_app_client, logged_in_rdu_user):
    # GIVEN a database with redirects in it
    add_redirect_rule(from_uri="generic", to_uri="new")
    add_redirect_rule(from_uri="generic/specific", to_uri="specific")
    add_redirect_rule(from_uri="lots/of/path/fragments", to_uri="blah")
    add_redirect_rule(from_uri="alphabetic/test", to_uri="specific")

    resp = test_app_client.get(url_for("redirects.index"))
    assert resp.status_code == 200
    xml_string = str(resp.data)

    # THEN the redirects are ordered with most path fragments first, and alphabetically within those groups.
    assert (
        xml_string.index("<KeyPrefixEquals>lots/of/path/fragments</KeyPrefixEquals>")
        < xml_string.index("<KeyPrefixEquals>alphabetic/test</KeyPrefixEquals>")
        < xml_string.index("<KeyPrefixEquals>generic/specific</KeyPrefixEquals>")
        < xml_string.index("<KeyPrefixEquals>generic</KeyPrefixEquals>")
    )

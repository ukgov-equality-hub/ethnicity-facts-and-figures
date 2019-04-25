from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Response, current_app
from flask_login import login_required

from application.redirects import redirects_blueprint
from application.redirects.models import Redirect


"""
This view generates all the necessary XML which can be copied into the
AWS static website hosting Redirection rules section

The process runs
1) Add/remove all redirects for the site using the redirect management commands
2) Build and deploy the static site
3) Copy and paste the contents of /redirects into the S3 redirection rules section

note: ensure the static build is complete before adding new redirect rules to S3
if these steps are carried out of order it is possible for a redirect a user to pages that don't exist yet

"""


def _build_routing_rules_xml(redirects):
    root = Element("RoutingRules")

    # Sort so that more specific redirects (i.e. with the most path fragments) are emitted first. Redirects with the
    # same number of path fragments are sorted alphabetically.
    # This prevents a more generic redirect rule, e.g. on `ethnicity-in-the-uk`, breaking the redirect
    # of a more specific rule, e.g. `ethnicity-in-the-uk/ethnic-groups-and-data-collected`.
    for r in sorted(redirects, key=lambda x: (-len(x.from_uri.split("/")), x.from_uri)):
        routing_rule = SubElement(root, "RoutingRule")

        condition = SubElement(routing_rule, "Condition")
        key_prefix = SubElement(condition, "KeyPrefixEquals")
        key_prefix.text = r.from_uri

        redirect = SubElement(routing_rule, "Redirect")
        replace_key_prefix = SubElement(redirect, "ReplaceKeyPrefixWith")
        replace_key_prefix.text = r.to_uri

        http_redirect_code = SubElement(redirect, "HttpRedirectCode")
        http_redirect_code.text = str(current_app.config["REDIRECT_HTTP_CODE"])

        redirect_hostname = SubElement(redirect, "HostName")
        redirect_hostname.text = current_app.config["REDIRECT_HOSTNAME"]

        redirect_protocol = SubElement(redirect, "Protocol")
        redirect_protocol.text = current_app.config["REDIRECT_PROTOCOL"]

    return tostring(root)


@redirects_blueprint.route("")
@login_required
def index():
    return Response(_build_routing_rules_xml(Redirect.query.all()), mimetype="text/xml")

from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Response, current_app
from flask_login import login_required

from application.redirects import redirects_blueprint
from application.redirects.models import Redirect


"""
This view generates all the necessary XML which can be copied into the
AWS static website hosting Redirection rules section

The process runs
1) Add/remove all redirects for the site using the redirect commands
2) Build and deploy the static site
3) Copy and paste the contents of /redirects into the S3 redirection rules section

note: ensure the static build is complete before adding new redirect rules to S3
if these steps are carried out of order it is possible for a redirect a user to pages that don't exist yet

"""


def _build_routing_rules_xml(redirects):
    root = Element('RoutingRules')

    for r in redirects:
        routing_rule = SubElement(root, 'RoutingRule')

        condition = SubElement(routing_rule, 'Condition')
        key_prefix = SubElement(condition, 'KeyPrefixEquals')
        key_prefix.text = r.from_uri

        redirect = SubElement(routing_rule, 'Redirect')
        replace_key_prefix = SubElement(redirect, 'ReplaceKeyPrefixWith')
        replace_key_prefix.text = r.to_uri
        http_redirect_code = SubElement(redirect, 'HttpRedirectCode')
        http_redirect_code.text = str(current_app.config['REDIRECT_HTTP_CODE'])

    return tostring(root)


@redirects_blueprint.route('/')
@login_required
def index():
    return Response(_build_routing_rules_xml(Redirect.query.all()), mimetype='text/xml')

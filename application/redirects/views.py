from xml.etree.ElementTree import Element, SubElement, tostring

from flask import Response, current_app
from flask_login import login_required

from application.redirects import redirects_blueprint
from application.redirects.models import Redirect


"""
This view generates all the necessary XML which can be copied into the
AWS static website hosting Redirection rules section

note: In a browser it is necessary to View Source to see the XML in its raw state
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


# TODO Better docs here
@redirects_blueprint.route('/')
@login_required
def index():
    return Response(_build_routing_rules_xml(Redirect.query.all()), mimetype='text/xml')

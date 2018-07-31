from flask_login import login_required

from application.redirects import redirects_blueprint
from application.redirects.models import Redirect

"""
This view generates all the necessary XML which can be copied into the
AWS static website hosting Redirection rules section

note: In a browser it is necessary to View Source to see the XML in its raw state
"""


# TODO Better docs here
@redirects_blueprint.route('/')
@login_required
def index():
    redirects = Redirect.query.all()
    routing_rules = '<RoutingRules>\n'
    for redirect in redirects:
        routing_rules += routing_rule_for_redirect(redirect)
        routing_rules += '\n'
    routing_rules += '</RoutingRules>'
    return routing_rules


def routing_rule_for_redirect(redirect):
    from flask import current_app

    routing_rule = '<RoutingRule>\n'
    routing_rule += '  <Condition>\n'
    routing_rule += '    <KeyPrefixEquals>' + redirect.from_uri + '</KeyPrefixEquals>\n'
    routing_rule += '  </Condition>\n'
    routing_rule += '  <Redirect>\n'
    routing_rule += '    <ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith>\n' % redirect.to_uri
    routing_rule += '    <HttpRedirectCode>%d</HttpRedirectCode>\n' % current_app.config['REDIRECT_HTTP_CODE']
    routing_rule += '  </Redirect>\n'
    routing_rule += '</RoutingRule>\n'
    return routing_rule

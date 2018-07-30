from flask_login import login_required

from application.redirects import redirects_blueprint
from application.redirects.models import Redirect


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
    routing_rule += '    <Protocol>%s</Protocol>\n' % current_app.config['REDIRECT_PROTOCOL']
    routing_rule += '    <HostName>%s</HostName>\n' % current_app.config['REDIRECT_HOSTNAME']
    routing_rule += '    <ReplaceKeyPrefixWith>%s</ReplaceKeyPrefixWith>\n' % redirect.to_uri
    routing_rule += '    <HttpRedirectCode>%d</HttpRedirectCode>\n' % current_app.config['REDIRECT_HTTP_CODE']
    routing_rule += '  </Redirect>\n'
    routing_rule += '</RoutingRule>\n'
    return routing_rule

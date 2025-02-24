from flask import current_app
from flask_httpauth import HTTPTokenAuth

from application.api import api_blueprint


auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):
    if current_app.config.get('EFF_API_TOKEN') is None:
        return False

    return token == current_app.config.get('EFF_API_TOKEN')


@api_blueprint.route("/foo")
@auth.login_required
def index():
    return "hello"

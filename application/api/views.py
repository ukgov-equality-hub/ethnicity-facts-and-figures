from flask import current_app, jsonify
from flask_httpauth import HTTPTokenAuth

from application.api import api_blueprint

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token: str) -> bool:
    if current_app.config.get('EFF_API_TOKEN') is None:
        return False

    return token == current_app.config.get('EFF_API_TOKEN')


@api_blueprint.route("/", methods=["GET"])
@auth.login_required
def index():
    return jsonify({
        'hello': 'world',
    })

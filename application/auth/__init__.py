from flask import Blueprint

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")

from application.auth.views import forgot_password  # noqa

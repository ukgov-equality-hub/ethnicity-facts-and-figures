from flask import Blueprint

register_blueprint = Blueprint('register', __name__, url_prefix='/register')

from application.register.views import confirm_account  # noqa

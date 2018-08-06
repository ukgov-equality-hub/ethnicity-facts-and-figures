from flask import Blueprint

redirects_blueprint = Blueprint('redirects', __name__, url_prefix='/redirects')

from application.redirects.views import index  # noqa

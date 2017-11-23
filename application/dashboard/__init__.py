from flask import Blueprint

dashboard_blueprint = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from application.dashboard.views import index  # noqa

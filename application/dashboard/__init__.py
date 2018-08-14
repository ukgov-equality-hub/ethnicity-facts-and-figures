from flask import Blueprint

dashboard_blueprint = Blueprint("dashboards", __name__, url_prefix="/dashboards")

from application.dashboard.views import index  # noqa

from flask import Blueprint

static_site_blueprint = Blueprint("static_site", __name__, url_prefix="/")

from application.static_site.views import index  # noqa

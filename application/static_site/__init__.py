from flask import Blueprint

static_site_blueprint = Blueprint('static_site', __name__)

from application.static_site.views import index  # noqa


@static_site_blueprint.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/'}


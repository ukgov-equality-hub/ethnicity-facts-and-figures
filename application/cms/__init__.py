from flask import Blueprint

cms_blueprint = Blueprint('cms', __name__, url_prefix='/cms')

from application.cms.views import create_measure_page  # noqa


@cms_blueprint.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/'}
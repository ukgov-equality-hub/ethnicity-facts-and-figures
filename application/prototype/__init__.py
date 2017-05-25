from flask import Blueprint

prototype_blueprint = Blueprint('prototype', __name__, url_prefix='/prototype')

from application.prototype.views import index  # noqa

@prototype_blueprint.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/'}


@prototype_blueprint.context_processor
def site_path_context_processor():
    return {'site_path': '/prototype'}

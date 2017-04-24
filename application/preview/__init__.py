from flask import Blueprint

preview_blueprint = Blueprint('preview', __name__,  url_prefix='/preview')

from application.preview.views import preview_page  # noqa


@preview_blueprint.context_processor
def asset_path_context_processor():
    return {'asset_path': '/static/govuk_template-0.20.0/assets/'}

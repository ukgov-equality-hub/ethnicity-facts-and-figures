from flask import Blueprint

static_site_blueprint = Blueprint('static_site',
                                  __name__,
                                  url_prefix='/site',
                                  template_folder='templates',
                                  static_folder='static')

from application.static_site.views import index  # noqa


@static_site_blueprint.context_processor
def asset_path_context_processor():
    return {'asset_path': '/site/static/'}


# TODO make path path configurable
@static_site_blueprint.context_processor
def site_path_context_processor():
    return {'site_path': '/site'}

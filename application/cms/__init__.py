from flask import Blueprint

cms_blueprint = Blueprint('cms', __name__)

from application.cms.views import index  # noqa

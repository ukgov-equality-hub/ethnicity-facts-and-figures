from flask import Blueprint

admin_blueprint = Blueprint("admin", __name__, url_prefix="/admin")

from application.admin.views import index  # noqa

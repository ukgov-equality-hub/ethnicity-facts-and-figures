from flask import Blueprint

audit_blueprint = Blueprint('audit', __name__, url_prefix='/audit')

from application.audit.views import index  # noqa

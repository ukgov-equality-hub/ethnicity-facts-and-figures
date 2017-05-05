from flask import render_template
from flask_login import login_required
from sqlalchemy import desc

from application.audit import audit_blueprint
from application.audit.models import Audit


@audit_blueprint.route('/')
@login_required
def index():
    audit_log = Audit.query.order_by(desc(Audit.timestamp)).all()
    return render_template('audit/index.html', audit_log=audit_log)

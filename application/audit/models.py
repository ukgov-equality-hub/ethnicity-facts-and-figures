from datetime import datetime
from application import db


class Audit(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user = db.Column(db.String(255))
    action = db.Column(db.Text())
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow())

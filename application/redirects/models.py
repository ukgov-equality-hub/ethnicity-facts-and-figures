from application import db


class Redirect(db.Model):
    created = db.Column(db.DateTime)
    from_uri = db.Column(db.String(255), primary_key=True, nullable=False)
    to_uri = db.Column(db.String(255), nullable=False)

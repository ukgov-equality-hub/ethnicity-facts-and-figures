from application import db


class Redirect(db.Model):
    guid = db.Column(db.String(255), primary_key=True)
    created = db.Column(db.DateTime)
    from_uri = db.Column(db.String(255))
    to_uri = db.Column(db.String(255))

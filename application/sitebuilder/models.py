from datetime import datetime
from sqlalchemy.dialects.postgresql import ENUM
from application import db


class Build(db.Model):

    created_at = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)
    status = db.Column(ENUM('PENDING', 'STARTED', 'DONE', 'SUPERSEDED', 'FAILED', name='build_status'),
                       default='PENDING',
                       nullable=False)
    succeeded_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.String, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)

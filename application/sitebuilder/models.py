from datetime import datetime

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from application import db


class Build(db.Model):

    __tablename__ = "build"
    __table_args__ = (PrimaryKeyConstraint("id", "created_at", name="build_pkey"), {})

    id = db.Column(UUID, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(
        ENUM("PENDING", "STARTED", "DONE", "SUPERSEDED", "FAILED", name="build_status"),
        default="PENDING",
        nullable=False,
    )
    succeeded_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.String, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)

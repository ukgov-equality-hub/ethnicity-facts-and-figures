from datetime import datetime
import enum

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from application import db


class BuildStatus(enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    DONE = "DONE"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"


class Build(db.Model):

    __tablename__ = "build"
    __table_args__ = (PrimaryKeyConstraint("id", "created_at", name="build_pkey"), {})

    id = db.Column(UUID, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum(BuildStatus, name="build_status"), default=BuildStatus.PENDING, nullable=False)
    succeeded_at = db.Column(db.DateTime, nullable=True)
    failure_reason = db.Column(db.String, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)

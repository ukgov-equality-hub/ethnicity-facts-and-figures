"""

These are Materialised Views

They should NEVER be imported into the manage.py otherwise alembic will try to generate
migrations to create tables for the objects

"""
from sqlalchemy import PrimaryKeyConstraint

from application import db


class LatestPublishedMeasureVersionByGeography(db.Model):
    __tablename__ = "latest_published_measure_versions_by_geography"

    topic_title = db.Column("topic_title", db.String())
    topic_slug = db.Column("topic_slug", db.String())
    subtopic_title = db.Column("subtopic_title", db.String())
    subtopic_slug = db.Column("subtopic_slug", db.String())
    subtopic_position = db.Column("subtopic_position", db.Integer())
    measure_slug = db.Column("measure_slug", db.String())
    measure_position = db.Column("measure_position", db.Integer())
    measure_version_id = db.Column("measure_version_id", db.Integer())
    measure_version_title = db.Column("measure_version_title", db.String())
    geography_name = db.Column("geography_name", db.String())
    geography_position = db.Column("geography_position", db.Integer())

    __table_args__ = (PrimaryKeyConstraint("measure_version_id"),)


class EthnicGroupByDimension(db.Model):
    __tablename__ = "ethnic_groups_by_dimension"

    topic_title = db.Column("topic_title", db.String())
    topic_slug = db.Column("topic_slug", db.String())
    subtopic_title = db.Column("subtopic_title", db.String())
    subtopic_slug = db.Column("subtopic_slug", db.String())
    subtopic_position = db.Column("subtopic_position", db.Integer())
    measure_id = db.Column("measure_id", db.Integer())
    measure_slug = db.Column("measure_slug", db.String())
    measure_position = db.Column("measure_position", db.Integer())
    measure_version_id = db.Column("measure_version_id", db.Integer())
    measure_version_title = db.Column("measure_version_title", db.String())
    dimension_guid = db.Column("dimension_guid", db.String())
    dimension_title = db.Column("dimension_title", db.String())
    dimension_position = db.Column("dimension_position", db.Integer())
    classification_title = db.Column("classification_title", db.String())
    ethnicity_value = db.Column("ethnicity_value", db.String())
    ethnicity_position = db.Column("ethnicity_position", db.Integer())

    __table_args__ = (
        PrimaryKeyConstraint("dimension_guid", "ethnicity_value", name="ethnic_groups_by_dimension_value_pk"),
    )


class ClassificationByDimension(db.Model):
    __tablename__ = "classifications_by_dimension"

    topic_title = db.Column("topic_title", db.String())
    topic_slug = db.Column("topic_slug", db.String())
    subtopic_title = db.Column("subtopic_title", db.String())
    subtopic_slug = db.Column("subtopic_slug", db.String())
    subtopic_position = db.Column("subtopic_position", db.Integer())
    measure_id = db.Column("measure_id", db.Integer())
    measure_slug = db.Column("measure_slug", db.String())
    measure_position = db.Column("measure_position", db.Integer())
    measure_version_id = db.Column("measure_version_id", db.Integer())
    measure_version_title = db.Column("measure_version_title", db.String())
    dimension_guid = db.Column("dimension_guid", db.String())
    dimension_title = db.Column("dimension_title", db.String())
    dimension_position = db.Column("dimension_position", db.Integer())
    classification_id = db.Column("classification_id", db.Integer())
    classification_title = db.Column("classification_title", db.String())
    classification_position = db.Column("classification_position", db.Integer())
    includes_parents = db.Column("includes_parents", db.Boolean())
    includes_all = db.Column("includes_all", db.Boolean())
    includes_unknown = db.Column("includes_unknown", db.Boolean())

    __table_args__ = (
        PrimaryKeyConstraint("dimension_guid", "classification_id", name="classification_by_dimension_value_pk"),
    )

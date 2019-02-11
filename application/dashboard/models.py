"""

These are Materialised Views

They should NEVER be imported into the manage.py otherwise alembic will try to generate
migrations to create tables for the objects

"""
from sqlalchemy import PrimaryKeyConstraint

from application import db


class LatestPublishedMeasureVersionByGeography(db.Model):
    __tablename__ = "new_latest_published_measure_versions_by_geography"

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

    subtopic_guid = db.Column("subtopic_guid", db.String())
    page_guid = db.Column("page_guid", db.String())
    page_title = db.Column("page_title", db.String())
    page_version = db.Column("page_version", db.String())
    page_status = db.Column("page_status", db.String())
    page_publication_date = db.Column("page_publication_date", db.Date())
    page_slug = db.Column("page_slug", db.String())
    page_position = db.Column("page_position", db.Integer())
    dimension_guid = db.Column("dimension_guid", db.String())
    dimension_title = db.Column("dimension_title", db.String())
    dimension_position = db.Column("dimension_position", db.Integer())
    categorisation = db.Column("categorisation", db.String())
    value = db.Column("value", db.String())
    value_position = db.Column("value_position", db.Integer())

    __table_args__ = (PrimaryKeyConstraint("dimension_guid", "value", name="ethnic_groups_by_dimension_value_pk"), {})


class CategorisationByDimension(db.Model):
    __tablename__ = "categorisations_by_dimension"

    subtopic_guid = db.Column("subtopic_guid", db.String())
    page_guid = db.Column("page_guid", db.String())
    page_title = db.Column("page_title", db.String())
    page_version = db.Column("page_version", db.String())
    page_slug = db.Column("page_slug", db.String())
    page_position = db.Column("page_position", db.Integer())
    dimension_guid = db.Column("dimension_guid", db.String())
    dimension_title = db.Column("dimension_title", db.String())
    dimension_position = db.Column("dimension_position", db.Integer())
    categorisation_id = db.Column("categorisation_id", db.Integer())
    categorisation = db.Column("categorisation", db.String())
    categorisation_position = db.Column("categorisation_position", db.Integer())
    includes_parents = db.Column("includes_parents", db.Boolean())
    includes_all = db.Column("includes_all", db.Boolean())
    includes_unknown = db.Column("includes_unknown", db.Boolean())

    __table_args__ = (
        PrimaryKeyConstraint("dimension_guid", "categorisation_id", name="categorisation_by_dimension_value_pk"),
        {},
    )

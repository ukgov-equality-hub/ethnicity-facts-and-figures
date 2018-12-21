"""

These are Materialised Views

They should NEVER be imported into the manage.py otherwise alembic will try to generate
migrations to create tables for the objects

"""
from sqlalchemy import PrimaryKeyConstraint

from application import db


class PageByLowestLevelOfGeography(db.Model):
    __tablename__ = "pages_by_geography"

    subtopic_guid = db.Column("subtopic_guid", db.String())
    page_guid = db.Column("page_guid", db.String())
    page_title = db.Column("page_title", db.String())
    page_version = db.Column("page_version", db.String())
    page_slug = db.Column("page_slug", db.String())
    page_position = db.Column("page_position", db.Integer())

    geography_name = db.Column("geography_name", db.String())
    geography_description = db.Column("geography_description", db.String())
    geography_position = db.Column("geography_position", db.Integer())

    __table_args__ = (PrimaryKeyConstraint("page_guid"), {})


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

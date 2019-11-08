"""Add Overseas region

Revision ID: 62308cd181b2
Revises: dimension_position_not_null
Create Date: 2019-11-08 15:58:57.694684

"""
from alembic import op
import sqlalchemy as sa

from application.dashboard.view_sql import (
    drop_all_dashboard_helper_views,
    latest_published_measure_versions_view,
    latest_published_measure_versions_by_geography_view,
    ethnic_groups_by_dimension_view,
    classifications_by_dimension,
)

# revision identifiers, used by Alembic.
revision = "62308cd181b2"
down_revision = "dimension_position_not_null"
branch_labels = None
depends_on = None

upgrade_lowest_level_of_geography = """
    UPDATE lowest_level_of_geography SET position =  2 WHERE name = 'United Kingdom';
    UPDATE lowest_level_of_geography SET position =  3 WHERE name = 'Country';
    UPDATE lowest_level_of_geography SET position =  4 WHERE name = 'Region';
    UPDATE lowest_level_of_geography SET position =  5 WHERE name = 'Local authority upper';
    UPDATE lowest_level_of_geography SET position =  6 WHERE name = 'Local authority lower';
    UPDATE lowest_level_of_geography SET position =  7 WHERE name = 'Police force area';
    UPDATE lowest_level_of_geography SET position =  8 WHERE name = 'Clinical commissioning group';
    UPDATE lowest_level_of_geography SET position =  9 WHERE name = 'Fire and rescue service area';
    INSERT INTO lowest_level_of_geography (name, position) VALUES ('UK and Overseas', 1);
"""

downgrade_lowest_level_of_geography = """
    DELETE FROM lowest_level_of_geography WHERE name = 'UK and Overseas';
    UPDATE lowest_level_of_geography SET position =  1 WHERE name = 'United Kingdom';
    UPDATE lowest_level_of_geography SET position =  2 WHERE name = 'Country';
    UPDATE lowest_level_of_geography SET position =  3 WHERE name = 'Region';
    UPDATE lowest_level_of_geography SET position =  4 WHERE name = 'Local authority upper';
    UPDATE lowest_level_of_geography SET position =  5 WHERE name = 'Local authority lower';
    UPDATE lowest_level_of_geography SET position =  6 WHERE name = 'Police force area';
    UPDATE lowest_level_of_geography SET position =  7 WHERE name = 'Clinical commissioning group';
    UPDATE lowest_level_of_geography SET position =  8 WHERE name = 'Fire and rescue service area';
"""

old_enum = ("ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND", "UK")
new_enum = old_enum + ("OVERSEAS",)

old_type = sa.Enum(*old_enum, name="uk_country_types")
new_type = sa.Enum(*new_enum, name="uk_country_types")
tmp_type = sa.Enum(*new_enum, name="uk_country_types_tmp")

tcr = sa.sql.table("measure_version", sa.Column("area_covered", new_type))


def upgrade():
    op.execute(drop_all_dashboard_helper_views)

    # Create a tempoary "_status" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        """ALTER TABLE measure_version ALTER COLUMN area_covered TYPE uk_country_types_tmp[]
                        USING area_covered::text[]::uk_country_types_tmp[]"""
    )

    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" status type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        """ALTER TABLE measure_version ALTER COLUMN area_covered TYPE uk_country_types[]
                        USING area_covered::text[]::uk_country_types[]"""
    )

    tmp_type.drop(op.get_bind(), checkfirst=False)

    op.get_bind()
    op.execute(upgrade_lowest_level_of_geography)

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)


def downgrade():
    op.execute(drop_all_dashboard_helper_views)

    # Create a tempoary "_status" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        """ALTER TABLE measure_version ALTER COLUMN area_covered TYPE uk_country_types_tmp[]
                        USING area_covered::text[]::uk_country_types_tmp[]"""
    )

    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" status type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute(
        """ALTER TABLE measure_version ALTER COLUMN area_covered TYPE uk_country_types[]
                        USING area_covered::text[]::uk_country_types[]"""
    )

    tmp_type.drop(op.get_bind(), checkfirst=False)

    op.get_bind()
    op.execute(downgrade_lowest_level_of_geography)

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)

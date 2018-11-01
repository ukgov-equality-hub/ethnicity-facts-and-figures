"""Removes some now-unused columns from the page table

   This is called "rebase migration" because it was originally intended to be overwritten by a "rebase migration" file
   that would have the same name but create all the database schema from scratch so we could delete all the earlier
   migration files to tidy things up a bit.

   We have since decided NOT to do that, but this has already been applied to live environments now so the name stays.

Revision ID: 2018_06_15_rebase_migration
Revises: 2018_05_14_share_pages
Create Date: 2018-06-15 08:47:32.766803

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from application.dashboard.view_sql_pre_categorisation_rename import (
    drop_all_dashboard_helper_views,
    latest_published_pages_view,
    pages_by_geography_view,
    ethnic_groups_by_dimension_view,
    categorisations_by_dimension,
)


# revision identifiers, used by Alembic.
revision = "2018_06_15_rebase_migration"
down_revision = "2018_05_14_share_pages"
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    op.drop_column("page", "ethnicity_definition_detail")
    op.drop_column("page", "secondary_source_1_publisher_text")
    op.drop_column("page", "suppression_rules")
    op.drop_column("page", "type_of_statistic")
    op.drop_column("page", "subtopics")
    op.drop_column("page", "frequency")
    op.drop_column("page", "disclosure_control")
    op.drop_column("page", "secondary_source_1_statistic_type")
    op.drop_column("page", "secondary_source_1_frequency")

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    op.add_column("page", sa.Column("secondary_source_1_frequency", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_statistic_type", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("disclosure_control", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("frequency", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("subtopics", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("type_of_statistic", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("suppression_rules", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_publisher_text", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("ethnicity_definition_detail", sa.TEXT(), autoincrement=False, nullable=True))

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

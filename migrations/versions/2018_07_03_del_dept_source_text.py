"""Drop department_source_text column from page table

This column is no longer used and should have been deleted as part of 2018_06_15_rebase_migration but was missed.

Revision ID: 2018_07_03_delete_dept_source_text
Revises: 2018_06_15_rebase_migration
Create Date: 2018-07-03 11:57:15.848554

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from application.dashboard.view_sql import (
    categorisations_by_dimension, drop_all_dashboard_helper_views, ethnic_groups_by_dimension_view,
    latest_published_pages_view, pages_by_geography_view
)

# revision identifiers, used by Alembic.
revision = '2018_07_03_del_dept_source_text'
down_revision = '2018_06_15_rebase_migration'
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    # Text values were converted from department_source_text to a department_source_id in revision addb446d684c
    # There are a few pages where the text value was not mapped to an org - these updates are to backfill
    # older versions of a page with missing department_source_id to match the most recent published version of the page

    op.execute('''
             UPDATE page SET department_source_id = 'EO1216' 
             WHERE department_source_text = 'Department for Education and Education and Skills Funding Agency'
             AND department_source_id IS NULL;

             UPDATE page SET department_source_id = 'D1198' 
             WHERE department_source_text = 'Start Up Loans Company'
             AND department_source_id IS NULL;
        ''')
    op.drop_column('page', 'department_source_text')

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    # We can re-create the column, but the previous data is lost
    op.add_column('page', sa.Column('department_source_text', sa.TEXT(), autoincrement=False, nullable=True))

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

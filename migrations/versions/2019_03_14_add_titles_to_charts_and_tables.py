"""Add titles to charts and tables

This is in preparation for storing the titles of charts and tables in
a separate database column, rather than as part of the JSON objects.

Revision ID: 2019_03_14_add_chart_table_titles
Revises: 2019_03_04_make_fields_nullable
Create Date: 2019-03-14 15:11:33.560576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb02568887b5'
down_revision = '2019_03_04_make_fields_nullable'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dimension_chart', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('dimension_table', sa.Column('title', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('dimension_table', 'title')
    op.drop_column('dimension_chart', 'title')

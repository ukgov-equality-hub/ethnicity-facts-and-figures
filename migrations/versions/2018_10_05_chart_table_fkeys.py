"""Add foreign keys from dimension to chart and table

Revision ID: 2018_10_05_chart_table_fkeys
Revises: 2018_10_04_code_is_id
Create Date: 2018-10-05 15:56:00.998752

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2018_10_05_chart_table_fkeys'
down_revision = '2018_10_04_code_is_id'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dimension', sa.Column('chart_id', sa.Integer(), nullable=True))
    op.add_column('dimension', sa.Column('table_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'dimension', 'dimension_chart', ['chart_id'], ['id'])
    op.create_foreign_key(None, 'dimension', 'dimension_table', ['table_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'dimension', type_='foreignkey')
    op.drop_constraint(None, 'dimension', type_='foreignkey')
    op.drop_column('dimension', 'table_id')
    op.drop_column('dimension', 'chart_id')

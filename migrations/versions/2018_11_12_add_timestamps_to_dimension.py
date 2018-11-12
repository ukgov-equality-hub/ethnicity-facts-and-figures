"""Add created and updated timestamps to dimensions

Revision ID: 90eef812019a
Revises: 2018_10_31_refactor_data_sources
Create Date: 2018-11-12 10:31:40.860099

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_11_12_dimension_timestamps"
down_revision = "2018_10_31_refactor_data_sources"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("dimension", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("dimension", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("dimension", "updated_at")
    op.drop_column("dimension", "created_at")

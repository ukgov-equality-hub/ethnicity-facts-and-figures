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
down_revision = "2018_11_12_data_source_purpose"
branch_labels = None
depends_on = None


def upgrade():

    # First add the timestamp columns with default NULL values
    op.execute("ALTER TABLE dimension ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE dimension ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE")

    # Now set the default values to the current UTC timestamp for future entries.
    op.execute("ALTER TABLE dimension ALTER COLUMN created_at SET DEFAULT timezone('utc', CURRENT_TIMESTAMP)")
    op.execute("ALTER TABLE dimension ALTER COLUMN updated_at SET DEFAULT timezone('utc', CURRENT_TIMESTAMP)")


def downgrade():
    op.drop_column("dimension", "updated_at")
    op.drop_column("dimension", "created_at")

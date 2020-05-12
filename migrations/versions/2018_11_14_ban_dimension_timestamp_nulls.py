"""ban_dimension_timestamp_nulls

Revision ID: aaaff196cfda
Revises: 2018_11_12_dimension_timestamps
Create Date: 2018-11-14 11:44:25.071102

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ban_dimension_timestamp_nulls"
down_revision = "2018_11_12_dimension_timestamps"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("dimension", "created_at", nullable=False)
    op.alter_column("dimension", "updated_at", nullable=False)


def downgrade():
    op.alter_column("dimension", "updated_at", nullable=True)
    op.alter_column("dimension", "created_at", nullable=True)

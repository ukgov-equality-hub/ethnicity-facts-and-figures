"""Rename from uix -> uq to follow naming convention

Revision ID: 2018_12_05_fix_page_constraint
Revises: 2018_12_05_fix_user_constraint
Create Date: 2018-12-05 18:43:24.009236

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_12_05_fix_page_constraint"
down_revision = "2018_12_05_fix_user_constraint"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_page_guid_version", "page", ["guid", "version"])
    op.drop_constraint("uix_page_guid_version", "page", type_="unique")


def downgrade():
    op.create_unique_constraint("uix_page_guid_version", "page", ["guid", "version"])
    op.drop_constraint("uq_page_guid_version", "page", type_="unique")

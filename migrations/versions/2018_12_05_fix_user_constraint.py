"""Rename unique constraint on users email address

Revision ID: 2018_12_05_fix_user_constraint
Revises: 2018_12_03_remove_duplicate_fkey
Create Date: 2018-12-05 18:29:33.749269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_12_05_fix_user_constraint"
down_revision = "2018_12_03_remove_duplicate_fkey"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.drop_constraint("users_email_key", "users", type_="unique")


def downgrade():
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_constraint("uq_users_email", "users", type_="unique")

"""Drop "family" column from classification table

Also adds not-null constraint to users table to match the current model.

Revision ID: 2018_10_03_drop_family
Revises: 2018_10_03_rename_cats
Create Date: 2018-10-03 17:45:33.189203

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_10_03_drop_family"
down_revision = "2018_10_03_rename_cats"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("classification", "family")
    op.alter_column(
        "users",
        "user_type",
        existing_type=postgresql.ENUM("RDU_USER", "DEPT_USER", "ADMIN_USER", "DEV_USER", name="type_of_user_types"),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "users",
        "user_type",
        existing_type=postgresql.ENUM("RDU_USER", "DEPT_USER", "ADMIN_USER", "DEV_USER", name="type_of_user_types"),
        nullable=True,
    )
    op.add_column("classification", sa.Column("family", sa.VARCHAR(length=255), autoincrement=False, nullable=True))

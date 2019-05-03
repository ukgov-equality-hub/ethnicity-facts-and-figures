"""Make organisation other_names and abbreviations arrays not nullable

Revision ID: 2019_04_05_not_null_orgs
Revises: 2019_04_01_fkey_cascades
Create Date: 2019-04-05 15:19:29.020479

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2019_04_05_not_null_orgs"
down_revision = "2019_04_01_fkey_cascades"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("organisation", "abbreviations", existing_type=postgresql.ARRAY(sa.VARCHAR()), nullable=False)
    op.alter_column("organisation", "other_names", existing_type=postgresql.ARRAY(sa.VARCHAR()), nullable=False)


def downgrade():
    op.alter_column("organisation", "other_names", existing_type=postgresql.ARRAY(sa.VARCHAR()), nullable=True)
    op.alter_column("organisation", "abbreviations", existing_type=postgresql.ARRAY(sa.VARCHAR()), nullable=True)

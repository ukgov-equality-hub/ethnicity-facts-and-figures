"""Make some fields on Chart and Table nullable

We want to copy chart and table data across to these tables but have no way to add a
classification for each one, so we'll have to live with some nulls in here.

Revision ID: 2019_03_04_make_fields_nullable
Revises: 2019_03_04_chart_table_settings
Create Date: 2019-03-05 16:38:12.835894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_03_04_make_fields_nullable"
down_revision = "2019_03_04_chart_table_settings"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("dimension_chart", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("dimension_chart", "includes_all", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_chart", "includes_parents", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_chart", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_table", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("dimension_table", "includes_all", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_table", "includes_parents", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_table", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=True)


def downgrade():
    op.alter_column("dimension_table", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "includes_parents", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "includes_all", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column("dimension_chart", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "includes_parents", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "includes_all", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False)

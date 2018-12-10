"""Make more fields in classification tables not nullable

Revision ID: 2018_12_05_not_nullable_fields
Revises: 2018_12_05_fix_page_constraint
Create Date: 2018-12-05 18:47:41.680614

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_12_05_not_nullable_fields"
down_revision = "2018_12_05_fix_page_constraint"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("dimension_categorisation", "includes_all", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_categorisation", "includes_parents", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_categorisation", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "includes_all", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "includes_parents", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_chart", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "includes_all", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "includes_parents", existing_type=sa.BOOLEAN(), nullable=False)
    op.alter_column("dimension_table", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=False)


def downgrade():
    op.alter_column("dimension_table", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_table", "includes_parents", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_table", "includes_all", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_chart", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_chart", "includes_parents", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_chart", "includes_all", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_categorisation", "includes_unknown", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_categorisation", "includes_parents", existing_type=sa.BOOLEAN(), nullable=True)
    op.alter_column("dimension_categorisation", "includes_all", existing_type=sa.BOOLEAN(), nullable=True)

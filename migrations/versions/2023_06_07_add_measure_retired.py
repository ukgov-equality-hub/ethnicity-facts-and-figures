"""empty message

Revision ID: 2023_06_07_add_measure_retired
Revises: 2021_07_13_source_data_view
Create Date: 2023-06-07 14:53:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2023_06_07_add_measure_retired"
down_revision = "2021_07_13_source_data_view"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("measure", sa.Column("retired", sa.Boolean(), nullable=True))
    op.execute("UPDATE measure SET retired = False;")
    op.alter_column("measure", "retired", existing_type=sa.Boolean(), nullable=False)
    op.execute("ALTER TABLE ONLY measure ALTER COLUMN retired SET DEFAULT False;")
    op.add_column("measure", sa.Column("replaced_by_measure_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "measure_replaced_by_measure_id_fkey",
        "measure",
        "measure",
        ["replaced_by_measure_id"],
        ["id"],
        ondelete="restrict",
    )


def downgrade():
    op.drop_column("measure", "retired")
    op.drop_column("measure", "replaced_by_measure_id")

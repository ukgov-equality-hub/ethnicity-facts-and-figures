"""Add unique constraint to MeasureVersion on Measure.id and Measure.version

Revision ID: 2019_01_15_uq_measure_version
Revises: 20181224_user_measure_table
Create Date: 2019-01-15 12:25:28.892266

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2019_01_15_uq_measure_version"
down_revision = "20181224_user_measure_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(op.f("uq_measure_version_measure_id"), "measure_version", ["measure_id", "version"])


def downgrade():
    op.drop_constraint(op.f("uq_measure_version_measure_id"), "measure_version", type_="unique")

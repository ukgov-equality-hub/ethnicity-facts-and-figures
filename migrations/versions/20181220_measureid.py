"""Add `measure_id` FK column to `measure_version` table

Revision ID: 20181220_measureid
Revises: 20181214_published_unpublished
Create Date: 2018-12-20 10:28:49.388878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20181220_measureid"
down_revision = "20181214_published_unpublished"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("measure_version", sa.Column("measure_id", sa.Integer(), nullable=True))
    op.create_foreign_key(op.f("measure_version_measure_id_fkey"), "measure_version", "measure", ["measure_id"], ["id"])


def downgrade():
    op.drop_constraint(op.f("measure_version_measure_id_fkey"), "measure_version", type_="foreignkey")
    op.drop_column("measure_version", "measure_id")

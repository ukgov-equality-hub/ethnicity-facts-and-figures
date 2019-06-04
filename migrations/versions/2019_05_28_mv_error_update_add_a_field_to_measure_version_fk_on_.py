"""Add a field to measure_version, fk on itself, to say which version an update is fixing

Revision ID: 2019_05_28_mv_error_update
Revises: 2019_04_18_add_topic_short_title
Create Date: 2019-05-28 08:31:21.119363

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_05_28_mv_error_update"
down_revision = "2019_04_18_add_topic_short_title"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("measure_version", sa.Column("update_corrects_measure_version", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("measure_version_update_corrects_measure_version_fkey"),
        "measure_version",
        "measure_version",
        ["update_corrects_measure_version"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        op.f("measure_version_update_corrects_measure_version_fkey"), "measure_version", type_="foreignkey"
    )
    op.drop_column("measure_version", "update_corrects_measure_version")

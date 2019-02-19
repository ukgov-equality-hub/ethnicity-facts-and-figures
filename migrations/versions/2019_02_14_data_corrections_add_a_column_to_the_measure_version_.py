"""Add a column to the measure_version table recording whether a minor update addresses a mistake in the data we
published

Revision ID: 2019_02_14_data_corrections
Revises: 2019_02_12_new_mat_views
Create Date: 2019-02-14 13:27:41.083950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_02_14_data_corrections"
down_revision = "2019_02_12_new_mat_views"
branch_labels = None
depends_on = None


def upgrade():
    measure_version = sa.Table(
        "measure_version", sa.MetaData(), sa.Column("update_corrects_data_mistake", sa.Boolean())
    )

    op.add_column("measure_version", sa.Column("update_corrects_data_mistake", sa.Boolean(), nullable=True))

    # This will lock the entire `measure_version` table, but at our scale this shouldn't be a concern as it won't lock
    # for very long at all, in reality.
    op.get_bind().execute(measure_version.update().values({"update_corrects_data_mistake": False}))


def downgrade():
    op.drop_column("measure_version", "update_corrects_data_mistake")

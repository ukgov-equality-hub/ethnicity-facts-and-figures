"""Rename `user_page` table to `user_measure`

Revision ID: 20181224_user_measure_table
Revises: 20181220_populate_measures
Create Date: 2018-12-24 09:52:07.668219

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20181224_user_measure_table"
down_revision = "20181220_populate_measures"
branch_labels = None
depends_on = None

max_measure_version_temp_table = """
CREATE TEMPORARY TABLE max_measure_version
AS
SELECT
    mv.*
FROM
    measure_version AS mv
WHERE
    mv.page_type = 'measure'
    AND mv.version = (
        SELECT
            MAX(version)
        FROM
            measure_version AS max_mv
        WHERE
            max_mv.guid = mv.guid);
"""

update_user_measure_table_with_measure_ids = """
UPDATE
    user_measure
SET
    measure_id = (
        SELECT
            max_measure_version.measure_id
        FROM
            max_measure_version
        WHERE max_measure_version.guid = user_measure.page_id
    )
"""

update_user_page_table_with_page_ids = """
UPDATE
    user_page
SET
    page_id = (
        SELECT
            max_measure_version.guid
        FROM
            max_measure_version
        WHERE max_measure_version.measure_id = user_page.measure_id
    )
"""


def upgrade():
    # rename table
    op.rename_table("user_page", "user_measure")

    # add new column
    op.add_column("user_measure", sa.Column("measure_id", sa.Integer(), nullable=True))

    # add FK constraint
    op.create_foreign_key(op.f("user_page_measure_id_fkey"), "user_measure", "measure", ["measure_id"], ["id"])

    # populate new column
    op.execute(max_measure_version_temp_table)
    op.execute(update_user_measure_table_with_measure_ids)

    # replace PK (user/page -> user/measure)
    op.drop_constraint(op.f("user_page_pkey"), "user_measure")
    op.create_primary_key(op.f("user_page_pkey"), "user_measure", ["user_id", "measure_id"])

    # ensure not nullable
    op.alter_column("user_measure", "measure_id", nullable=False)

    # drop old column
    op.drop_column("user_measure", "page_id")

    # remove temp table
    op.execute("DROP TABLE max_measure_version")


def downgrade():
    # rename table
    op.rename_table("user_measure", "user_page")

    # add old column
    op.add_column("user_page", sa.Column("page_id", sa.String(), nullable=True))

    # populate old column
    op.execute(max_measure_version_temp_table)
    op.execute(update_user_page_table_with_page_ids)

    # replace PK (user/measure -> user/page)
    op.drop_constraint(op.f("user_page_pkey"), "user_page")
    op.create_primary_key(op.f("user_page_pkey"), "user_page", ["user_id", "page_id"])

    # ensure not nullable
    op.alter_column("user_page", "page_id", nullable=False)

    # drop new column
    op.drop_column("user_page", "measure_id")

    # remove temp table
    op.execute("DROP TABLE max_measure_version")

"""Remove now-unused Chart and Table fields from Dimension

Revision ID: 2019_03_20_tidy_up_dimension
Revises: 2019_03_04_make_fields_nullable
Create Date: 2019-03-20 10:42:37.514429

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2019_03_20_tidy_up_dimension"
down_revision = "2019_03_04_make_fields_nullable"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("dimension", "table_source_data")
    op.drop_column("dimension", "chart_source_data")
    op.drop_column("dimension", "chart_builder_version")
    op.drop_column("dimension", "table_builder_version")
    op.drop_column("dimension", "table")
    op.drop_column("dimension", "chart")
    op.drop_column("dimension", "table_2_source_data")
    op.drop_column("dimension", "chart_2_source_data")


def downgrade():
    op.add_column(
        "dimension",
        sa.Column("chart_2_source_data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "dimension",
        sa.Column("table_2_source_data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "dimension", sa.Column("chart", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True)
    )
    op.add_column(
        "dimension", sa.Column("table", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True)
    )
    op.add_column("dimension", sa.Column("table_builder_version", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column("dimension", sa.Column("chart_builder_version", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column(
        "dimension",
        sa.Column("chart_source_data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )
    op.add_column(
        "dimension",
        sa.Column("table_source_data", postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    )

    # It should be possible to re-populate the restored fields in the following way...
    # If this turns out to be necessary, do it as a data migration script:
    # * Copy dimension_chart.settings_and_source_data into chart_2_source_data
    # * Copy dimension_table.settings_and_source_data into table_2_source_data
    # * Copy dimension_chart.chart_object into chart
    # * Copy dimension_table.table_object into table
    # * Set all entries in chart_builder_version and table_builder_version to 2
    # * Leave chart_source_data and table_source_data as NULL

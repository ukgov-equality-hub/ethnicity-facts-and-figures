"""Add new columnsto the Chart and Table models, to store chart/table settings objects and built chart/table objects
   The data to populate these will be moved from the Dimension model by a data migration.

Revision ID: 2019_03_04_chart_table_settings
Revises: 2019_02_22_clean_data_model
Create Date: 2019-03-05 12:49:58.938371

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2019_03_04_chart_table_settings"
down_revision = "2019_02_22_clean_data_model"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "dimension_chart", sa.Column("settings_and_source_data", postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    op.add_column("dimension_chart", sa.Column("built_object", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "dimension_table", sa.Column("settings_and_source_data", postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
    op.add_column("dimension_table", sa.Column("built_object", postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column("dimension_table", "built_object")
    op.drop_column("dimension_table", "settings_and_source_data")
    op.drop_column("dimension_chart", "built_object")
    op.drop_column("dimension_chart", "settings_and_source_data")

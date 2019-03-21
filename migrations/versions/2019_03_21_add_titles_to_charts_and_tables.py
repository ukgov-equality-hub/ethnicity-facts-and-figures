"""Add titles to charts and tables

This is in preparation for storing the titles of charts and tables in
a separate database column, rather than as part of the JSON objects.

Revision ID: 2019_03_21_add_titles
Revises: 2019_03_20_tidy_up_dimension
Create Date: 2019-03-14 15:11:33.560576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_03_21_add_titles"
down_revision = "2019_03_20_tidy_up_dimension"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("dimension_chart", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("dimension_table", sa.Column("title", sa.String(length=255), nullable=True))

    op.execute(
        "UPDATE dimension_chart SET title = settings_and_source_data::JSON->'chartFormat'->>'chart_title'::TEXT;"
    )
    op.execute(
        "UPDATE dimension_table SET title = settings_and_source_data::JSON->'tableValues'->>'table_title'::TEXT;"
    )


def downgrade():
    op.drop_column("dimension_table", "title")
    op.drop_column("dimension_chart", "title")

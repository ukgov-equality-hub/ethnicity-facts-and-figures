"""
Add new "dimension_chart" and "dimension_table" tables.
These will initially be used to hold just the ethnicity classifications of charts and tables of a dimension.
In future the chart and table data itself will be moved from the dimension tables into these new tables.

Revision ID: 2018_09_18_classifications
Revises: 2018_09_25_add_long_title
Create Date: 2018-09-18 14:02:04.242855

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_09_18_classifications"
down_revision = "2018_09_25_add_long_title"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "dimension_chart",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("categorisation_id", sa.Integer(), nullable=True),
        sa.Column("includes_all", sa.Boolean(), nullable=True),
        sa.Column("includes_parents", sa.Boolean(), nullable=True),
        sa.Column("includes_unknown", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["categorisation_id"], ["categorisation.id"], name="dimension_chart_categorisation_fkey"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dimension_table",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("categorisation_id", sa.Integer(), nullable=True),
        sa.Column("includes_all", sa.Boolean(), nullable=True),
        sa.Column("includes_parents", sa.Boolean(), nullable=True),
        sa.Column("includes_unknown", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["categorisation_id"], ["categorisation.id"], name="dimension_table_categorisation_fkey"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("dimension_chart")
    op.drop_table("dimension_table")

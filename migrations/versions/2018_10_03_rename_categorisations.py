"""Rename 'Categorisation' to 'Classification'

This also renames CategorisationValue to Ethnicity, as all our categories
represent ethnicities.

The join tables 'association' and 'parent_association' are renamed to
'ethnicity_in_classification' and 'parent_ethnicity_in_classification'.


Revision ID: 2018_10_03_rename_categorisations
Revises: 2018_10_02_chart_and_table
Create Date: 2018-10-03 15:10:17.882656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_10_03_rename_cats"
down_revision = "2018_10_02_chart_and_table"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("association", "ethnicity_in_classification")
    op.rename_table("parent_association", "parent_ethnicity_in_classification")
    op.rename_table("categorisation_value", "ethnicity")
    op.rename_table("categorisation", "classification")

    op.alter_column("ethnicity_in_classification", "categorisation_id", new_column_name="classification_id")
    op.alter_column("ethnicity_in_classification", "categorisation_value_id", new_column_name="ethnicity_id")

    op.alter_column("parent_ethnicity_in_classification", "categorisation_id", new_column_name="classification_id")
    op.alter_column("parent_ethnicity_in_classification", "categorisation_value_id", new_column_name="ethnicity_id")

    op.alter_column("dimension_categorisation", "categorisation_id", new_column_name="classification_id")
    op.alter_column("dimension_chart", "categorisation_id", new_column_name="classification_id")
    op.alter_column("dimension_table", "categorisation_id", new_column_name="classification_id")

    op.execute("ALTER SEQUENCE categorisation_id_seq RENAME TO classification_id_seq")
    op.execute("ALTER SEQUENCE categorisation_value_id_seq RENAME TO ethnicity_id_seq")

    op.execute("ALTER INDEX categorisation_pkey RENAME TO classification_pkey")
    op.execute("ALTER INDEX categorisation_value_pkey RENAME TO ethnicity_pkey")


def downgrade():
    op.execute("ALTER SEQUENCE classification_id_seq RENAME TO categorisation_id_seq")
    op.execute("ALTER SEQUENCE ethnicity_id_seq RENAME TO categorisation_value_id_seq")

    op.execute("ALTER INDEX classification_pkey RENAME TO categorisation_pkey")
    op.execute("ALTER INDEX ethnicity_pkey RENAME TO categorisation_value_pkey")

    op.alter_column("dimension_table", "classification_id", new_column_name="categorisation_id")

    op.alter_column("dimension_chart", "classification_id", new_column_name="categorisation_id")

    op.alter_column("dimension_categorisation", "classification_id", new_column_name="categorisation_id")

    op.alter_column("parent_ethnicity_in_classification", "classification_id", new_column_name="categorisation_id")
    op.alter_column("parent_ethnicity_in_classification", "ethnicity_id", new_column_name="categorisation_value_id")

    op.alter_column("ethnicity_in_classification", "classification_id", new_column_name="categorisation_id")
    op.alter_column("ethnicity_in_classification", "ethnicity_id", new_column_name="categorisation_value_id")

    op.rename_table("classification", "categorisation")
    op.rename_table("ethnicity", "categorisation_value")
    op.rename_table("parent_ethnicity_in_classification", "parent_association")
    op.rename_table("ethnicity_in_classification", "association")

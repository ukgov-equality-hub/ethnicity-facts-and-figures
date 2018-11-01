"""
Make the current "code" column the primary key and id column for "classification"

Revision ID: 2018_10_04_code_is_id
Revises: 2018_10_03_drop_family
Create Date: 2018-10-04 14:32:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from application.dashboard.view_sql import (
    categorisations_by_dimension,
    drop_all_dashboard_helper_views,
    ethnic_groups_by_dimension_view,
    latest_published_pages_view,
    pages_by_geography_view,
)

# revision identifiers, used by Alembic.
revision = "2018_10_04_code_is_id"
down_revision = "2018_10_03_drop_family"
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    # Add uniqueness constraint on "code"
    op.create_unique_constraint("uq_classification_code", "classification", ["code"])

    # Add "classification_code" column to all charts that currently have classification_id as a foreign key
    # Code is defined as String(length=255) in the original migration that set it up, so use the same here
    op.add_column("dimension_categorisation", sa.Column("classification_code", sa.String(length=255), nullable=True))
    op.add_column("dimension_chart", sa.Column("classification_code", sa.String(length=255), nullable=True))
    op.add_column("dimension_table", sa.Column("classification_code", sa.String(length=255), nullable=True))
    op.add_column("ethnicity_in_classification", sa.Column("classification_code", sa.String(length=255), nullable=True))
    op.add_column(
        "parent_ethnicity_in_classification", sa.Column("classification_code", sa.String(length=255), nullable=True)
    )

    # Backfill values for "classification_code"
    op.execute(
        """
        UPDATE dimension_categorisation
        SET classification_code =
            (SELECT code FROM classification
             WHERE id = dimension_categorisation.classification_id)
        """
    )

    op.execute(
        """
        UPDATE dimension_chart
        SET classification_code =
            (SELECT code FROM classification
             WHERE id = dimension_chart.classification_id)
        """
    )

    op.execute(
        """
        UPDATE dimension_table
        SET classification_code =
            (SELECT code FROM classification
             WHERE id = dimension_table.classification_id)
        """
    )

    op.execute(
        """
        UPDATE ethnicity_in_classification
        SET classification_code =
            (SELECT code FROM classification
             WHERE id = ethnicity_in_classification.classification_id)
        """
    )

    op.execute(
        """
        UPDATE parent_ethnicity_in_classification
        SET classification_code =
            (SELECT code FROM classification
            WHERE id = parent_ethnicity_in_classification.classification_id)
        """
    )

    # Drop dimension_categorisation primary key
    op.drop_constraint("dimension_categorisation_pkey", "dimension_categorisation", type_="primary")

    # Drop classification foreign keys
    op.drop_constraint("categorisation_dimension_categorisation_fkey", "dimension_categorisation", type_="foreignkey")

    op.drop_constraint("dimension_chart_categorisation_fkey", "dimension_chart", type_="foreignkey")
    op.drop_constraint("dimension_table_categorisation_fkey", "dimension_table", type_="foreignkey")
    op.drop_constraint("categorisation_association_fkey", "ethnicity_in_classification", type_="foreignkey")
    op.drop_constraint(
        "categorisation_parent_association_fkey", "parent_ethnicity_in_classification", type_="foreignkey"
    )

    # Drop the id column from classification
    op.drop_constraint("classification_pkey", "classification", type_="primary")
    op.drop_column("classification", "id")

    # Rename "code" to "id"
    op.alter_column("classification", "code", nullable=False, new_column_name="id")

    # Make "id" the primary key
    op.create_primary_key("classification_pkey", "classification", ["id"])

    # Drop the old classification_id columns from referencing tables
    op.drop_column("dimension_categorisation", "classification_id")
    op.drop_column("dimension_chart", "classification_id")
    op.drop_column("dimension_table", "classification_id")
    op.drop_column("ethnicity_in_classification", "classification_id")
    op.drop_column("parent_ethnicity_in_classification", "classification_id")

    # Rename the classification_code columns to classification_id and make them non-nullable
    op.alter_column(
        "dimension_categorisation", "classification_code", nullable=False, new_column_name="classification_id"
    )
    op.alter_column("dimension_chart", "classification_code", nullable=False, new_column_name="classification_id")
    op.alter_column("dimension_table", "classification_code", nullable=False, new_column_name="classification_id")
    op.alter_column(
        "ethnicity_in_classification", "classification_code", nullable=False, new_column_name="classification_id"
    )
    op.alter_column(
        "parent_ethnicity_in_classification", "classification_code", nullable=False, new_column_name="classification_id"
    )

    # Add foreign key constraints to the classification_id columns
    op.create_foreign_key(
        "dimension_categorisation_classification_fkey",
        "dimension_categorisation",
        "classification",
        ["classification_id"],
        ["id"],
    )
    op.create_foreign_key(
        "dimension_chart_classification_fkey", "dimension_chart", "classification", ["classification_id"], ["id"]
    )
    op.create_foreign_key(
        "dimension_table_classification_fkey", "dimension_table", "classification", ["classification_id"], ["id"]
    )
    op.create_foreign_key(
        "ethnicity_in_classification_classification_fkey",
        "ethnicity_in_classification",
        "classification",
        ["classification_id"],
        ["id"],
    )
    op.create_foreign_key(
        "parent_ethnicity_in_classification_classification_fkey",
        "parent_ethnicity_in_classification",
        "classification",
        ["classification_id"],
        ["id"],
    )

    # Add updated primary key to dimension_categorisation
    op.create_primary_key(
        "dimension_categorisation_pkey", "dimension_categorisation", ["dimension_guid", "classification_id"]
    )

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    # Drop primary key from dimension_categorisation
    op.drop_constraint("dimension_categorisation_pkey", "dimension_categorisation", type_="primary")

    # Drop foreign key constraints on classification_id columns
    op.drop_constraint(
        "parent_ethnicity_in_classification_classification_fkey",
        "parent_ethnicity_in_classification",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ethnicity_in_classification_classification_fkey", "ethnicity_in_classification", type_="foreignkey"
    )
    op.drop_constraint("dimension_table_classification_fkey", "dimension_table", type_="foreignkey")
    op.drop_constraint("dimension_chart_classification_fkey", "dimension_chart", type_="foreignkey")
    op.drop_constraint("dimension_categorisation_classification_fkey", "dimension_categorisation", type_="foreignkey")

    # Rename the classification_id columns to classification_code and make them nullable
    op.alter_column(
        "dimension_categorisation", "classification_id", nullable=True, new_column_name="classification_code"
    )
    op.alter_column("dimension_chart", "classification_id", nullable=True, new_column_name="classification_code")
    op.alter_column("dimension_table", "classification_id", nullable=True, new_column_name="classification_code")
    op.alter_column(
        "ethnicity_in_classification", "classification_id", nullable=True, new_column_name="classification_code"
    )
    op.alter_column(
        "parent_ethnicity_in_classification", "classification_id", nullable=True, new_column_name="classification_code"
    )

    # Add classification_id columns to referencing tables
    op.add_column("dimension_categorisation", sa.Column("classification_id", sa.Integer(), nullable=True))
    op.add_column("dimension_chart", sa.Column("classification_id", sa.Integer(), nullable=True))
    op.add_column("dimension_table", sa.Column("classification_id", sa.Integer(), nullable=True))
    op.add_column("ethnicity_in_classification", sa.Column("classification_id", sa.Integer(), nullable=True))
    op.add_column("parent_ethnicity_in_classification", sa.Column("classification_id", sa.Integer(), nullable=True))

    # TODO - fill in these steps!
    # Rename id to code in classification table
    op.alter_column("classification", "id", nullable=False, new_column_name="code")

    # Drop the old primary key based on code
    op.drop_constraint("classification_pkey", "classification", type_="primary")

    # Add a new id column acting as a primary key with autoincrement.
    op.execute("ALTER TABLE classification ADD COLUMN id SERIAL PRIMARY KEY;")

    # Backfill the classification_id fields on referencing tables
    op.execute(
        """
        UPDATE dimension_categorisation
        SET classification_id =
            (SELECT id FROM classification
             WHERE code = dimension_categorisation.classification_code)
        """
    )

    op.execute(
        """
        UPDATE dimension_chart
        SET classification_id =
            (SELECT id FROM classification
             WHERE code = dimension_chart.classification_code)
        """
    )

    op.execute(
        """
        UPDATE dimension_table
        SET classification_id =
            (SELECT id FROM classification
             WHERE code = dimension_table.classification_code)
        """
    )

    op.execute(
        """
        UPDATE ethnicity_in_classification
        SET classification_id =
            (SELECT id FROM classification
             WHERE code = ethnicity_in_classification.classification_code)
        """
    )

    op.execute(
        """
        UPDATE parent_ethnicity_in_classification
        SET classification_id =
            (SELECT id FROM classification
            WHERE code = parent_ethnicity_in_classification.classification_code)
        """
    )

    # Make the classification_id columns not nullable now that they've all been backfilled.
    op.alter_column("parent_ethnicity_in_classification", "classification_id", nullable=False)

    op.alter_column("ethnicity_in_classification", "classification_id", nullable=False)

    op.alter_column("dimension_table", "classification_id", nullable=False)

    op.alter_column("dimension_chart", "classification_id", nullable=False)

    op.alter_column("dimension_categorisation", "classification_id", nullable=False)

    # Add foreign key constraints to the classification_id columns
    op.create_foreign_key(
        "categorisation_dimension_categorisation_fkey",
        "dimension_categorisation",
        "classification",
        ["classification_id"],
        ["id"],
    )
    op.create_foreign_key(
        "dimension_chart_categorisation_fkey", "dimension_chart", "classification", ["classification_id"], ["id"]
    )
    op.create_foreign_key(
        "dimension_table_categorisation_fkey", "dimension_table", "classification", ["classification_id"], ["id"]
    )
    op.create_foreign_key(
        "categorisation_association_fkey",
        "ethnicity_in_classification",
        "classification",
        ["classification_id"],
        ["id"],
    )
    op.create_foreign_key(
        "categorisation_parent_association_fkey",
        "parent_ethnicity_in_classification",
        "classification",
        ["classification_id"],
        ["id"],
    )

    # Delete all the classification_code fields from referencing tables
    op.drop_column("parent_ethnicity_in_classification", "classification_code")
    op.drop_column("ethnicity_in_classification", "classification_code")
    op.drop_column("dimension_table", "classification_code")
    op.drop_column("dimension_chart", "classification_code")
    op.drop_column("dimension_categorisation", "classification_code")

    # Remove the uniqueness constraint on code
    op.drop_constraint("uq_classification_code", "classification", type_="unique")

    # Add updated primary key to dimension_categorisation
    op.create_primary_key(
        "dimension_categorisation_pkey", "dimension_categorisation", ["dimension_guid", "classification_id"]
    )

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

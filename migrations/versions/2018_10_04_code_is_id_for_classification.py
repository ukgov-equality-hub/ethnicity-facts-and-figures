"""
Make the current "code" column the primary key and id column for "classification"

Revision ID: 2018_10_04_code_is_id
Revises: 2018_10_03_drop_family
Create Date: 2018-10-04 14:32:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

drop_all_dashboard_helper_views = """
    DROP INDEX IF EXISTS uix_pages_by_geography;
    DROP INDEX IF EXISTS uix_latest_published_pages;
    DROP INDEX IF EXISTS uix_ethnic_groups_by_dimension;
    DROP INDEX IF EXISTS uix_categorisations_by_dimension;
    DROP MATERIALIZED VIEW pages_by_geography;
    DROP MATERIALIZED VIEW latest_published_pages;
    DROP MATERIALIZED VIEW ethnic_groups_by_dimension;
    DROP MATERIALIZED VIEW categorisations_by_dimension;
"""

latest_published_pages_view = """
    CREATE
    MATERIALIZED
    VIEW
    latest_published_pages as (SELECT p.*
     FROM page p
     JOIN ( SELECT latest_arr.guid,
            (latest_arr.version_arr[1] || '.'::text) || latest_arr.version_arr[2] AS version
           FROM ( SELECT page.guid,
                    max(string_to_array(page.version::text, '.'::text)::integer[]) AS version_arr
                   FROM page
                  WHERE page.status::text = 'APPROVED'::text
                  GROUP BY page.guid) latest_arr) latest_published ON p.guid::text = latest_published.guid::text AND p.version::text = latest_published.version);

    CREATE UNIQUE INDEX uix_latest_published_pages ON latest_published_pages (guid);
"""  # noqa

pages_by_geography_view = """
    CREATE
    MATERIALIZED
    VIEW
    pages_by_geography as (SELECT subtopic.guid AS "subtopic_guid",
        p.guid AS "page_guid",
        p.title AS "page_title",
        p.version AS "page_version",
        p.uri AS "page_uri",
        p.position AS "page_position",
        geog.name AS "geography_name",
        geog.description AS "geography_description",
        geog.position AS "geography_position"
    FROM latest_published_pages p
    JOIN page subtopic ON p.parent_guid = subtopic.guid
    JOIN lowest_level_of_geography geog ON p.lowest_level_of_geography_id = geog.name
    ORDER BY geog.position ASC);

    CREATE UNIQUE INDEX uix_pages_by_geography ON pages_by_geography (page_guid);
"""  # noqa


ethnic_groups_by_dimension_view = """
    CREATE
    MATERIALIZED
    VIEW ethnic_groups_by_dimension as ( SELECT all_page_value_connections.* FROM
      (
            (
              SELECT subtopic.guid AS "subtopic_guid",
              p.guid AS "page_guid",
              p.title AS "page_title",
              p.version AS "page_version",
              p.status AS "page_status",
              p.publication_date AS "page_publication_date",
              p.uri AS "page_uri",
              p.position AS "page_position",
              d.guid AS "dimension_guid",
              d.title AS "dimension_title",
              d.position AS "dimension_position",
              c.title AS "categorisation",
              ethnic_group.value AS "value",
              ethnic_group.position AS "value_position"
              FROM page p
              JOIN page subtopic ON p.parent_guid = subtopic.guid
              JOIN dimension d ON d.page_id = p.guid AND d.page_version = p.version
              JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
              JOIN classification c ON dc.classification_id = c.id
              JOIN ethnicity_in_classification ethnic_group_as_child ON c.id = ethnic_group_as_child.classification_id
              JOIN ethnicity ethnic_group ON ethnic_group_as_child.ethnicity_id = ethnic_group.id
              )
            UNION
            (
                  SELECT subtopic.guid AS "subtopic_guid",
                  p.guid AS "page_guid",
                  p.title AS "page_title",
                  p.version AS "page_version",
                  p.status AS "page_status",
                  p.publication_date AS "page_publication_date",
                  p.uri AS "page_uri",
                  p.position AS "page_position",
                  d.guid AS "dimension_guid",
                  d.title AS "dimension_title",
                  d.position AS "dimension_position",
                  c.title AS "categorisation",
                  ethnic_group.value AS "value",
                  ethnic_group.position AS "value_position"
                  FROM page p
                  JOIN page subtopic ON p.parent_guid = subtopic.guid
                  JOIN dimension d ON d.page_id = p.guid AND d.page_version = p.version
                  JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
                  JOIN classification c ON dc.classification_id = c.id
                  JOIN parent_ethnicity_in_classification ethnic_group_as_parent ON c.id = ethnic_group_as_parent.classification_id
                  JOIN ethnicity ethnic_group ON ethnic_group_as_parent.ethnicity_id = ethnic_group.id
                  WHERE dc.includes_parents
            )
      ) AS all_page_value_connections
      JOIN
      (SELECT guid, version_arr[1] || '.' || version_arr[2] AS "version" FROM
        (SELECT guid, MAX(string_to_array(version, '.')::int[]) AS "version_arr"
          FROM page
          WHERE status = 'APPROVED'
          GROUP BY guid
        ) AS latest_arr
      ) AS latest
      ON all_page_value_connections.page_guid = latest.guid AND all_page_value_connections.page_version = latest.version
    );

    CREATE UNIQUE INDEX uix_ethnic_groups_by_dimension ON ethnic_groups_by_dimension (dimension_guid, value);
"""  # noqa


categorisations_by_dimension = """
        CREATE
        MATERIALIZED
        VIEW
        categorisations_by_dimension as ( SELECT all_dimension_categorisations.* FROM
      (
            (
              SELECT subtopic.guid AS "subtopic_guid",
              p.guid AS "page_guid",
              p.title AS "page_title",
              p.version AS "page_version",
              p.uri AS "page_uri",
              p.position AS "page_position",
              d.guid AS "dimension_guid",
              d.title AS "dimension_title",
              d.position AS "dimension_position",
              c.id AS "categorisation_id",
              c.title AS "categorisation",
              c.position AS "categorisation_position",
              dc.includes_parents AS "includes_parents",
              dc.includes_all AS "includes_all",
              dc.includes_unknown AS "includes_unknown"
              FROM page p
              JOIN page subtopic ON p.parent_guid = subtopic.guid
              JOIN dimension d ON d.page_id = p.guid AND d.page_version = p.version
              JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
              JOIN classification c ON dc.classification_id = c.id
              )
      ) AS all_dimension_categorisations
      JOIN
      (SELECT guid, version_arr[1] || '.' || version_arr[2] AS "version" FROM
        (SELECT guid, MAX(string_to_array(version, '.')::int[]) AS "version_arr"
          FROM page
          WHERE status = 'APPROVED'
          GROUP BY guid
        ) AS latest_arr
      ) AS latest
      ON all_dimension_categorisations.page_guid = latest.guid AND all_dimension_categorisations.page_version = latest.version
    );

     CREATE UNIQUE INDEX uix_categorisations_by_dimension ON categorisations_by_dimension (dimension_guid, categorisation_id);
"""  # noqa


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

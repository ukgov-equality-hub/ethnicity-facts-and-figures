"""Remove old `data source` attributes from the monolith page table

Revision ID: 2018_11_19_clean_page_sources
Revises: ban_dimension_timestamp_nulls
Create Date: 2018-11-20 12:08:43.201032

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_11_19_clean_page_sources"
down_revision = "ban_dimension_timestamp_nulls"
branch_labels = None
depends_on = None


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


def upgrade():
    op.execute(drop_all_dashboard_helper_views)

    op.drop_constraint("type_of_statistic_fkey", "page", type_="foreignkey")
    op.drop_constraint("secondary_source_1_type_of_statistic_fkey", "page", type_="foreignkey")
    op.drop_constraint("organisation_secondary_source_1_fkey", "page", type_="foreignkey")
    op.drop_constraint("frequency_secondary_source_1_fkey", "page", type_="foreignkey")
    op.drop_constraint("page_dept_source_id_organisation_fkey", "page", type_="foreignkey")
    op.drop_constraint("frequency_of_release_fkey", "page", type_="foreignkey")
    op.drop_column("page", "secondary_source_1_type_of_statistic_id")
    op.drop_column("page", "published_date")
    op.drop_column("page", "secondary_source_1_data_source_purpose")
    op.drop_column("page", "type_of_statistic_id")
    op.drop_column("page", "secondary_source_1_frequency_id")
    op.drop_column("page", "secondary_source_1_type_of_data")
    op.drop_column("page", "data_source_purpose")
    op.drop_column("page", "frequency_id")
    op.drop_column("page", "secondary_source_1_publisher_id")
    op.drop_column("page", "secondary_source_1_date")
    op.drop_column("page", "source_url")
    op.drop_column("page", "source_text")
    op.drop_column("page", "frequency_other")
    op.drop_column("page", "type_of_data")
    op.drop_column("page", "secondary_source_1_frequency_other")
    op.drop_column("page", "secondary_source_1_note_on_corrections_or_updates")
    op.drop_column("page", "note_on_corrections_or_updates")
    op.drop_column("page", "secondary_source_1_title")
    op.drop_column("page", "department_source_id")
    op.drop_column("page", "secondary_source_1_url")

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():
    op.execute(drop_all_dashboard_helper_views)

    op.add_column("page", sa.Column("secondary_source_1_url", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("department_source_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_title", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("note_on_corrections_or_updates", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column(
        "page",
        sa.Column("secondary_source_1_note_on_corrections_or_updates", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "page",
        sa.Column("secondary_source_1_frequency_other", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.add_column(
        "page",
        sa.Column(
            "type_of_data",
            postgresql.ARRAY(postgresql.ENUM("ADMINISTRATIVE", "SURVEY", name="type_of_data_types")),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column("page", sa.Column("frequency_other", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("source_text", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("source_url", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_date", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column(
        "page", sa.Column("secondary_source_1_publisher_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True)
    )
    op.add_column("page", sa.Column("frequency_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("data_source_purpose", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column(
        "page",
        sa.Column(
            "secondary_source_1_type_of_data",
            postgresql.ARRAY(postgresql.ENUM("ADMINISTRATIVE", "SURVEY", name="type_of_data_types")),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "page", sa.Column("secondary_source_1_frequency_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.add_column("page", sa.Column("type_of_statistic_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column(
        "page", sa.Column("secondary_source_1_data_source_purpose", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.add_column("page", sa.Column("published_date", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column(
        "page", sa.Column("secondary_source_1_type_of_statistic_id", sa.INTEGER(), autoincrement=False, nullable=True)
    )
    op.create_foreign_key("frequency_of_release_fkey", "page", "frequency_of_release", ["frequency_id"], ["id"])
    op.create_foreign_key(
        "page_dept_source_id_organisation_fkey", "page", "organisation", ["department_source_id"], ["id"]
    )
    op.create_foreign_key(
        "frequency_secondary_source_1_fkey", "page", "frequency_of_release", ["secondary_source_1_frequency_id"], ["id"]
    )
    op.create_foreign_key(
        "organisation_secondary_source_1_fkey", "page", "organisation", ["secondary_source_1_publisher_id"], ["id"]
    )
    op.create_foreign_key(
        "secondary_source_1_type_of_statistic_fkey",
        "page",
        "type_of_statistic",
        ["secondary_source_1_type_of_statistic_id"],
        ["id"],
    )
    op.create_foreign_key("type_of_statistic_fkey", "page", "type_of_statistic", ["type_of_statistic_id"], ["id"])

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

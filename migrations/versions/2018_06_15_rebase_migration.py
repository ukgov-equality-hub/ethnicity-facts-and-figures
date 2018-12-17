"""Removes some now-unused columns from the page table

   This is called "rebase migration" because it was originally intended to be overwritten by a "rebase migration" file
   that would have the same name but create all the database schema from scratch so we could delete all the earlier
   migration files to tidy things up a bit.

   We have since decided NOT to do that, but this has already been applied to live environments now so the name stays.

Revision ID: 2018_06_15_rebase_migration
Revises: 2018_05_14_share_pages
Create Date: 2018-06-15 08:47:32.766803

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

refresh_all_dashboard_helper_views = """
    REFRESH MATERIALIZED VIEW CONCURRENTLY latest_published_pages;
    REFRESH MATERIALIZED VIEW CONCURRENTLY pages_by_geography;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ethnic_groups_by_dimension;
    REFRESH MATERIALIZED VIEW CONCURRENTLY categorisations_by_dimension;
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
              JOIN categorisation c ON dc.categorisation_id = c.id
              JOIN association ethnic_group_as_child ON c.id = ethnic_group_as_child.categorisation_id
              JOIN categorisation_value ethnic_group ON ethnic_group_as_child.categorisation_value_id = ethnic_group.id
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
                  JOIN categorisation c ON dc.categorisation_id = c.id
                  JOIN parent_association ethnic_group_as_parent ON c.id = ethnic_group_as_parent.categorisation_id
                  JOIN categorisation_value ethnic_group ON ethnic_group_as_parent.categorisation_value_id = ethnic_group.id
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
              JOIN categorisation c ON dc.categorisation_id = c.id
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
revision = "2018_06_15_rebase_migration"
down_revision = "2018_05_14_share_pages"
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    op.drop_column("page", "ethnicity_definition_detail")
    op.drop_column("page", "secondary_source_1_publisher_text")
    op.drop_column("page", "suppression_rules")
    op.drop_column("page", "type_of_statistic")
    op.drop_column("page", "subtopics")
    op.drop_column("page", "frequency")
    op.drop_column("page", "disclosure_control")
    op.drop_column("page", "secondary_source_1_statistic_type")
    op.drop_column("page", "secondary_source_1_frequency")

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():

    op.get_bind()
    op.execute(drop_all_dashboard_helper_views)

    op.add_column("page", sa.Column("secondary_source_1_frequency", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_statistic_type", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("disclosure_control", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("frequency", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("subtopics", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("type_of_statistic", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("suppression_rules", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("secondary_source_1_publisher_text", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("page", sa.Column("ethnicity_definition_detail", sa.TEXT(), autoincrement=False, nullable=True))

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

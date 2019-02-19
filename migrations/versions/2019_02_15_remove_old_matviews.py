"""Remove the now-unused matviews based on the old data model

Revision ID: 2019_02_15_remove_old_matviews
Revises: 2019_02_14_data_corrections
Create Date: 2019-01-15 12:25:28.892266

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2019_02_15_remove_old_matviews"
down_revision = "2019_02_14_data_corrections"
branch_labels = None
depends_on = None

drop_old_materialized_views = """
DROP INDEX IF EXISTS uix_latest_published_pages;
DROP INDEX IF EXISTS uix_pages_by_geography;
DROP INDEX IF EXISTS uix_ethnic_groups_by_dimension;
DROP INDEX IF EXISTS uix_categorisations_by_dimension;
DROP MATERIALIZED VIEW IF EXISTS pages_by_geography CASCADE;
DROP MATERIALIZED VIEW IF EXISTS ethnic_groups_by_dimension CASCADE;
DROP MATERIALIZED VIEW IF EXISTS categorisations_by_dimension CASCADE;
DROP MATERIALIZED VIEW IF EXISTS latest_published_pages CASCADE;
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
    op.execute(drop_old_materialized_views)


def downgrade():
    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)

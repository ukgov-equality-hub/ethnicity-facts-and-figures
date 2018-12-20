"""empty message

Revision ID: 18a2aea8ea85
Revises: 20181214_published_unpublished
Create Date: 2018-12-20 10:52:50.641092

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_uri_slug'
down_revision = '20181220_measureid'
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
    latest_published_pages as (SELECT mv.*
     FROM measure_version mv
     JOIN ( SELECT latest_arr.guid,
            (latest_arr.version_arr[1] || '.'::text) || latest_arr.version_arr[2] AS version
           FROM ( SELECT measure_version.guid,
                    max(string_to_array(measure_version.version::text, '.'::text)::integer[]) AS version_arr
                   FROM measure_version
                  WHERE measure_version.status::text = 'APPROVED'::text
                  GROUP BY measure_version.guid) latest_arr) latest_published ON mv.guid::text = latest_published.guid::text AND mv.version::text = latest_published.version);

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
        p.slug AS "page_slug",
        p.position AS "page_position",
        geog.name AS "geography_name",
        geog.description AS "geography_description",
        geog.position AS "geography_position"
    FROM latest_published_pages p
    JOIN measure_version subtopic ON p.parent_guid = subtopic.guid
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
              mv.guid AS "page_guid",
              mv.title AS "page_title",
              mv.version AS "page_version",
              mv.status AS "page_status",
              mv.published_at AS "page_publication_date",
              mv.slug AS "page_slug",
              mv.position AS "page_position",
              d.guid AS "dimension_guid",
              d.title AS "dimension_title",
              d.position AS "dimension_position",
              c.title AS "categorisation",
              ethnic_group.value AS "value",
              ethnic_group.position AS "value_position"
              FROM measure_version mv
              JOIN measure_version subtopic ON mv.parent_guid = subtopic.guid
              JOIN dimension d ON d.page_id = mv.guid AND d.page_version = mv.version
              JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
              JOIN classification c ON dc.classification_id = c.id
              JOIN ethnicity_in_classification ethnic_group_as_child ON c.id = ethnic_group_as_child.classification_id
              JOIN ethnicity ethnic_group ON ethnic_group_as_child.ethnicity_id = ethnic_group.id
              )
            UNION
            (
                  SELECT subtopic.guid AS "subtopic_guid",
                  mv.guid AS "page_guid",
                  mv.title AS "page_title",
                  mv.version AS "page_version",
                  mv.status AS "page_status",
                  mv.published_at AS "page_publication_date",
                  mv.slug AS "page_slug",
                  mv.position AS "page_position",
                  d.guid AS "dimension_guid",
                  d.title AS "dimension_title",
                  d.position AS "dimension_position",
                  c.title AS "categorisation",
                  ethnic_group.value AS "value",
                  ethnic_group.position AS "value_position"
                  FROM measure_version mv
                  JOIN measure_version subtopic ON mv.parent_guid = subtopic.guid
                  JOIN dimension d ON d.page_id = mv.guid AND d.page_version = mv.version
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
          FROM measure_version
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
              mv.guid AS "page_guid",
              mv.title AS "page_title",
              mv.version AS "page_version",
              mv.slug AS "page_slug",
              mv.position AS "page_position",
              d.guid AS "dimension_guid",
              d.title AS "dimension_title",
              d.position AS "dimension_position",
              c.id AS "categorisation_id",
              c.title AS "categorisation",
              c.position AS "categorisation_position",
              dc.includes_parents AS "includes_parents",
              dc.includes_all AS "includes_all",
              dc.includes_unknown AS "includes_unknown"
              FROM measure_version mv
              JOIN measure_version subtopic ON mv.parent_guid = subtopic.guid
              JOIN dimension d ON d.page_id = mv.guid AND d.page_version = mv.version
              JOIN dimension_categorisation dc ON d.guid = dc.dimension_guid
              JOIN classification c ON dc.classification_id = c.id
              )
      ) AS all_dimension_categorisations
      JOIN
      (SELECT guid, version_arr[1] || '.' || version_arr[2] AS "version" FROM
        (SELECT guid, MAX(string_to_array(version, '.')::int[]) AS "version_arr"
          FROM measure_version
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
    op.alter_column('measure_version', 'uri', new_column_name='slug')
    op.alter_column('measure', 'uri', new_column_name='slug')
    op.alter_column('topic', 'uri', new_column_name='slug')
    op.alter_column('subtopic', 'uri', new_column_name='slug')

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():
    op.alter_column('measure_version', 'slug', new_column_name='uri')
    op.alter_column('measure', 'slug', new_column_name='uri')
    op.alter_column('topic', 'slug', new_column_name='uri')
    op.alter_column('subtopic', 'slug', new_column_name='uri')


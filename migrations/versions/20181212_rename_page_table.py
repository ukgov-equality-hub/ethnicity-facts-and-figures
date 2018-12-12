"""Rename page table to `measure_version` and other changes cascading from that

This migration will require publisher downtime as it will lock pretty much the entire database - and is not backwards
compatible.

Revision ID: 20181212_rename_page_table
Revises: 20181211_topic_subtopic_measure
Create Date: 2018-12-03 10:51:52.822365

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import Sequence, CreateSequence, DropSequence

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

NEW_latest_published_pages_view = """
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

NEW_pages_by_geography_view = """
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
    JOIN measure_version subtopic ON p.parent_guid = subtopic.guid
    JOIN lowest_level_of_geography geog ON p.lowest_level_of_geography_id = geog.name
    ORDER BY geog.position ASC);

    CREATE UNIQUE INDEX uix_pages_by_geography ON pages_by_geography (page_guid);
"""  # noqa


NEW_ethnic_groups_by_dimension_view = """
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
              mv.publication_date AS "page_publication_date",
              mv.uri AS "page_uri",
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
                  mv.publication_date AS "page_publication_date",
                  mv.uri AS "page_uri",
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


NEW_categorisations_by_dimension = """
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
              mv.uri AS "page_uri",
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


OLD_latest_published_pages_view = """
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

OLD_pages_by_geography_view = """
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


OLD_ethnic_groups_by_dimension_view = """
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


OLD_categorisations_by_dimension = """
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
revision = "20181212_rename_page_table"
down_revision = "20181211_topic_subtopic_measure"
branch_labels = None
depends_on = None


def upgrade():
    # Drop materialized views
    op.execute(drop_all_dashboard_helper_views)

    # * remove constraints
    op.drop_constraint("data_source_in_page_page_guid_fkey", "data_source_in_page", type_="foreignkey")
    op.drop_constraint("dimension_page_id_version_fkey", "dimension", type_="foreignkey")
    op.drop_constraint("upload_page_id_version_fkey", "upload", type_="foreignkey")
    op.drop_constraint("page_parent_guid_version_fkey", "page", type_="foreignkey")
    op.drop_constraint("uq_page_guid_version", "page", type_="unique")
    op.drop_constraint("page_guid_version_pkey", "page", type_="primary")
    op.drop_constraint("data_source_id_page_guid_version_pk", "data_source_in_page", type_="primary")

    # * create `measure_version_id_seq`
    op.execute(CreateSequence(Sequence("measure_version_id_seq")))

    # * add columns
    #   * `id` to `page`, not nullable, default next from `measure_version_id_seq`
    op.add_column(
        "page",
        sa.Column(
            "id", sa.Integer(), nullable=False, server_default=sa.text("nextval('measure_version_id_seq'::regclass)")
        ),
    )
    op.add_column("page", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.add_column("data_source_in_page", sa.Column("measure_version_id", sa.Integer(), nullable=True))
    op.add_column("upload", sa.Column("measure_version_id", sa.Integer(), nullable=True))
    op.add_column("dimension", sa.Column("measure_version_id", sa.Integer(), nullable=True))

    conn = op.get_bind()

    conn.execute(
        """
UPDATE
    page AS measure
SET
    parent_id = (
        SELECT
            subtopic.id
        FROM
            page AS subtopic
        WHERE
            measure.parent_guid = subtopic.guid
            AND measure.parent_version = subtopic.version
            AND subtopic.page_type = 'subtopic')
WHERE
    measure.page_type = 'measure'
        """
    )
    conn.execute(
        """
UPDATE
    page AS subtopic
SET
    parent_id = (
        SELECT
            topic.id
        FROM
            page AS topic
        WHERE
            subtopic.parent_guid = topic.guid
            AND subtopic.parent_version = topic.version
            AND topic.page_type = 'topic')
WHERE
    subtopic.page_type = 'subtopic'
        """
    )
    conn.execute(
        """
UPDATE
    page AS topic
SET
    parent_id = (
        SELECT
            homepage.id
        FROM
            page AS homepage
        WHERE
            topic.parent_guid = homepage.guid
            AND topic.parent_version = homepage.version
            AND homepage.page_type = 'homepage')
WHERE
    topic.page_type = 'topic'
        """
    )
    conn.execute(
        """
UPDATE
    upload
SET
    measure_version_id = (
        SELECT
            page.id
        FROM
            page
        WHERE
            upload.page_id = page.guid
            AND upload.page_version = page.version)
        """
    )
    conn.execute(
        """
UPDATE
    dimension
SET
    measure_version_id = (
        SELECT
            page.id
        FROM
            page
        WHERE
            dimension.page_id = page.guid
            AND dimension.page_version = page.version)
        """
    )
    conn.execute(
        """
UPDATE
    data_source_in_page
SET
    measure_version_id = (
        SELECT
            page.id
        FROM
            page
        WHERE
            data_source_in_page.page_guid = page.guid
            AND data_source_in_page.page_version = page.version)
        """
    )

    op.alter_column("data_source_in_page", "measure_version_id", nullable=False)
    op.alter_column("upload", "measure_version_id", nullable=False)
    op.alter_column("dimension", "measure_version_id", nullable=False)

    # * rename tables:
    op.rename_table("page", "measure_version")
    op.rename_table("data_source_in_page", "data_source_in_measure_version")

    # * add constraints back
    # * Add foreign key and not nullable constraints to `data_source_in_page`, `upload`, `dimension`
    op.create_primary_key(op.f("measure_version_id_pkey"), "measure_version", ["id", "guid", "version"])
    op.create_primary_key(
        op.f("data_source_in_measure_version_data_source_id_pkey"),
        "data_source_in_measure_version",
        ["data_source_id", "measure_version_id"],
    )

    op.create_foreign_key(
        op.f("measure_version_parent_id_fkey"),
        "measure_version",
        "measure_version",
        ["parent_id", "parent_guid", "parent_version"],
        ["id", "guid", "version"],
    )
    op.create_foreign_key(
        op.f("upload_measure_version_id_fkey"),
        "upload",
        "measure_version",
        ["measure_version_id", "page_id", "page_version"],
        ["id", "guid", "version"],
    )
    op.create_foreign_key(
        op.f("dimension_measure_version_id_fkey"),
        "dimension",
        "measure_version",
        ["measure_version_id", "page_id", "page_version"],
        ["id", "guid", "version"],
    )

    op.create_foreign_key(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        "measure_version",
        ["measure_version_id", "page_guid", "page_version"],
        ["id", "guid", "version"],
    )

    # Create materialized views using new spec
    op.execute(NEW_latest_published_pages_view)
    op.execute(NEW_ethnic_groups_by_dimension_view)
    op.execute(NEW_categorisations_by_dimension)
    op.execute(NEW_pages_by_geography_view)


def downgrade():
    # Drop materialized views
    op.execute(drop_all_dashboard_helper_views)

    op.drop_constraint(
        "data_source_in_measure_version_measure_version_id_fkey", "data_source_in_measure_version", type_="foreignkey"
    )
    op.drop_constraint("dimension_measure_version_id_fkey", "dimension", type_="foreignkey")
    op.drop_constraint("upload_measure_version_id_fkey", "upload", type_="foreignkey")
    op.drop_constraint("measure_version_parent_id_fkey", "measure_version", type_="foreignkey")
    op.drop_constraint(
        "data_source_in_measure_version_data_source_id_pkey", "data_source_in_measure_version", type_="primary"
    )
    op.drop_constraint("measure_version_id_pkey", "measure_version", type_="primary")

    op.rename_table("data_source_in_measure_version", "data_source_in_page")
    op.rename_table("measure_version", "page")

    op.drop_column("dimension", "measure_version_id")
    op.drop_column("upload", "measure_version_id")
    op.drop_column("data_source_in_page", "measure_version_id")
    op.drop_column("page", "parent_id")
    op.drop_column("page", "id")

    op.execute(DropSequence(Sequence("measure_version_id_seq")))

    op.create_unique_constraint("uq_page_guid_version", "page", ["guid", "version"])

    op.create_primary_key(op.f("page_guid_version_pkey"), "page", ["guid", "version"])
    op.create_primary_key(
        op.f("data_source_id_page_guid_version_pk"),
        "data_source_in_page",
        ["data_source_id", "page_guid", "page_version"],
    )

    op.create_foreign_key(
        op.f("data_source_in_page_page_guid_fkey"),
        "data_source_in_page",
        "page",
        ["page_guid", "page_version"],
        ["guid", "version"],
    )
    op.create_foreign_key(
        op.f("dimension_page_id_version_fkey"), "dimension", "page", ["page_id", "page_version"], ["guid", "version"]
    )
    op.create_foreign_key(
        op.f("upload_page_id_version_fkey"), "upload", "page", ["page_id", "page_version"], ["guid", "version"]
    )
    op.create_foreign_key(
        op.f("page_parent_guid_version_fkey"), "page", "page", ["parent_guid", "parent_version"], ["guid", "version"]
    )

    # Create materialized views using old (pre-migration) spec
    op.execute(OLD_latest_published_pages_view)
    op.execute(OLD_ethnic_groups_by_dimension_view)
    op.execute(OLD_categorisations_by_dimension)
    op.execute(OLD_pages_by_geography_view)

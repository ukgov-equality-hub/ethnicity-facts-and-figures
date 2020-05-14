""" 2018_04_25_migrate_geog_view

Revision ID: 20180425_migrate_geography_view
Revises: 2018_03_22_user_model_refactor
Create Date: 2018-04-12 11:36:07.395067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_04_25_migrate_geog_view"
down_revision = "2018_04_20_data_src_refactor"
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()

    op.execute(
        """
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
                  GROUP BY page.guid) latest_arr) latest_published ON p.guid::text = latest_published.guid::text AND p.version::text = latest_published.version)
        """
    )

    op.execute(
        """
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
        ORDER BY geog.position ASC)
    """
    )

    op.execute(
        """
        CREATE
        UNIQUE INDEX
        uix_pages_by_geography
        ON pages_by_geography (page_guid)
    """
    )

    op.execute(
        """
        CREATE
        UNIQUE INDEX
        uix_latest_published_pages
        ON latest_published_pages (guid)
    """
    )


def downgrade():
    op.get_bind()
    op.execute("DROP INDEX IF EXISTS uix_pages_by_geography;")
    op.execute("DROP INDEX IF EXISTS uix_latest_published_pages;")
    op.execute("DROP MATERIALIZED VIEW pages_by_geography;")
    op.execute("DROP MATERIALIZED VIEW latest_published_pages;")

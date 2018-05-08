"""Make contact details 2 per page rather than 2 per source

Revision ID: 2018_05_04_coalesce_contacts
Revises: 2018_04_25_migrate_geog_view
Create Date: 2018-05-04 11:36:02.088310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2018_05_04_coalesce_contacts'
down_revision = '2018_04_25_migrate_geog_view'
branch_labels = None
depends_on = None


def upgrade():
    # The latest_published_pages materialized view depends on columns that we want to drop, so need to drop it first
    _drop_dependent_views()

    # Create new columns for second page-level contact details
    op.alter_column('page', 'contact_email', type_=sa.TEXT())
    op.alter_column('page', 'contact_name', type_=sa.TEXT())
    op.alter_column('page', 'contact_phone', type_=sa.TEXT())
    op.add_column('page', sa.Column('contact_2_email', sa.TEXT(), nullable=True))
    op.add_column('page', sa.Column('contact_2_name', sa.TEXT(), nullable=True))
    op.add_column('page', sa.Column('contact_2_phone', sa.TEXT(), nullable=True))

    # Copy any existing second contact details into the new columns from wherever it can be found
    # There is currently no data in any of the "secondary_source_1_contact_2_..." fields, so ignore these
    op.get_bind()
    op.execute("""
        UPDATE page
        SET contact_2_email = subquery.email,
            contact_2_name = subquery.name,
            contact_2_phone = subquery.phone
        FROM (SELECT 
                  guid, 
                  version, 
                  COALESCE(NULLIF(primary_source_contact_2_email,''),NULLIF(secondary_source_1_contact_1_email,''))
                      AS email,
                  COALESCE(NULLIF(primary_source_contact_2_name,''),NULLIF(secondary_source_1_contact_1_name,''))
                      AS name,
                  COALESCE(NULLIF(primary_source_contact_2_phone,''),NULLIF(secondary_source_1_contact_1_phone,''))
                      AS phone
              FROM page
        ) AS subquery
        WHERE page.guid = subquery.guid AND page.version = subquery.version;
    """)

    # Drop the source-related contact columns
    op.drop_column('page', 'primary_source_contact_2_name')
    op.drop_column('page', 'primary_source_contact_2_email')
    op.drop_column('page', 'primary_source_contact_2_phone')
    op.drop_column('page', 'secondary_source_1_contact_1_name')
    op.drop_column('page', 'secondary_source_1_contact_1_email')
    op.drop_column('page', 'secondary_source_1_contact_1_phone')
    op.drop_column('page', 'secondary_source_1_contact_2_name')
    op.drop_column('page', 'secondary_source_1_contact_2_email')
    op.drop_column('page', 'secondary_source_1_contact_2_phone')

    # Recreate latest_published_pages and it's associated index
    _create_dependent_views()


def downgrade():
    # Remove the "new style" latest_published_pages
    _drop_dependent_views()

    # We can re-add the previously dropped columns but there is no way to populate them with the "Contact 2" data
    op.add_column('page', sa.Column('primary_source_contact_2_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('primary_source_contact_2_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('primary_source_contact_2_phone', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_phone', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_phone', sa.TEXT(), autoincrement=False, nullable=True))

    # Drop the "Contact 2" columns, losing all "Contact 2" data
    op.drop_column('page', 'contact_2_phone')
    op.drop_column('page', 'contact_2_name')
    op.drop_column('page', 'contact_2_email')

    # Revert column type for contact details
    op.alter_column('page', 'contact_email', type_=sa.String(length=255))
    op.alter_column('page', 'contact_name', type_=sa.String(length=255))
    op.alter_column('page', 'contact_phone', type_=sa.String(length=255))

    # Recreate latest_published_pages and it's associated index in the previous format
    _create_dependent_views()


def _drop_dependent_views():
    # pages_by_geography depends on latest_published_pages so need to drop that first, too
    op.get_bind()
    op.execute('DROP INDEX IF EXISTS uix_pages_by_geography;')
    op.execute('DROP INDEX IF EXISTS uix_latest_published_pages;')
    op.execute('DROP MATERIALIZED VIEW pages_by_geography;')
    op.execute('DROP MATERIALIZED VIEW latest_published_pages;')


def _create_dependent_views():
    # CREATE MATERIALIZED VIEW queries copied from "2018_04_25_migrate_geog_view"
    op.get_bind()
    op.execute('''
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
    ''')

    op.execute('''
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
    ''')

    op.execute('''
        CREATE
        UNIQUE INDEX
        uix_pages_by_geography
        ON pages_by_geography (page_guid)
    ''')

    op.execute('''
        CREATE
        UNIQUE INDEX
        uix_latest_published_pages
        ON latest_published_pages (guid)
    ''')

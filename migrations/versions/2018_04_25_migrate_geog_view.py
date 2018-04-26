""" 2018_04_25_migrate_geog_view

Revision ID: 20180425_migrate_geography_view
Revises: 2018_03_22_user_model_refactor
Create Date: 2018-04-12 11:36:07.395067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2018_04_25_migrate_geog_view'
down_revision = '2018_04_11_add_sandbox_topic'
branch_labels = None
depends_on = None


def upgrade():

    op.get_bind()

    op.execute('''
    CREATE
    MATERIALIZED
    VIEW
    latest_published_pages as (SELECT p.guid,
        p.uri,
        p.description,
        p.page_type,
        p.status,
        p.parent_guid,
        p.publication_date,
        p.published,
        p.contact_email,
        p.contact_name,
        p.contact_phone,
        p.data_source_purpose,
        p.department_source_text,
        p.disclosure_control,
        p.estimation,
        p.ethnicity_definition_detail,
        p.ethnicity_definition_summary,
        p.frequency,
        p.further_technical_information,
        p.last_update_date,
        p.measure_summary,
        p.methodology,
        p.need_to_know,
        p.next_update_date,
        p.published_date,
        p.qmi_url,
        p.related_publications,
        p.source_text,
        p.source_url,
        p.subtopics,
        p.summary,
        p.suppression_rules,
        p.time_covered,
        p.title,
        p.type_of_statistic,
        p.parent_version,
        p.version,
        p.created_at,
        p.updated_at,
        p.external_edit_summary,
        p.internal_edit_summary,
        p.secondary_source_1_contact_1_email,
        p.secondary_source_1_contact_1_name,
        p.secondary_source_1_contact_1_phone,
        p.secondary_source_1_contact_2_email,
        p.secondary_source_1_contact_2_name,
        p.secondary_source_1_contact_2_phone,
        p.secondary_source_1_date,
        p.secondary_source_1_date_next_update,
        p.secondary_source_1_date_updated,
        p.secondary_source_1_disclosure_control,
        p.secondary_source_1_frequency,
        p.secondary_source_1_publisher_text,
        p.secondary_source_1_statistic_type,
        p.secondary_source_1_suppression_rules,
        p.secondary_source_1_title,
        p.secondary_source_1_url,
        p.secondary_source_2_contact_1_email,
        p.secondary_source_2_contact_1_name,
        p.secondary_source_2_contact_1_phone,
        p.secondary_source_2_contact_2_email,
        p.secondary_source_2_contact_2_name,
        p.secondary_source_2_contact_2_phone,
        p.secondary_source_2_date,
        p.secondary_source_2_date_next_update,
        p.secondary_source_2_date_updated,
        p.secondary_source_2_disclosure_control,
        p.secondary_source_2_frequency,
        p.secondary_source_2_publisher_text,
        p.secondary_source_2_statistic_type,
        p.secondary_source_2_suppression_rules,
        p.secondary_source_2_title,
        p.secondary_source_2_url,
        p.primary_source_contact_2_email,
        p.primary_source_contact_2_name,
        p.primary_source_contact_2_phone,
        p."position",
        p.additional_description,
        p.created_by,
        p.last_updated_by,
        p.published_by,
        p.unpublished_by,
        p.db_version_id,
        p.type_of_data,
        p.frequency_id,
        p.frequency_other,
        p.type_of_statistic_id,
        p.secondary_source_1_type_of_statistic_id,
        p.secondary_source_2_type_of_statistic_id,
        p.area_covered,
        p.department_source_id,
        p.lowest_level_of_geography_id,
        p.review_token,
        p.secondary_source_1_frequency_id,
        p.secondary_source_1_frequency_other,
        p.secondary_source_1_publisher_id,
        p.secondary_source_2_frequency_id,
        p.secondary_source_2_frequency_other,
        p.secondary_source_2_publisher_id,
        p.internal_reference,
        p.latest
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

def downgrade():
    op.get_bind()
    op.execute('DROP INDEX IF EXISTS uix_pages_by_geography;')
    op.execute('DROP INDEX IF EXISTS uix_latest_published_pages;')
    op.execute('DROP MATERIALIZED VIEW pages_by_geography;')
    op.execute('DROP MATERIALIZED VIEW latest_published_pages;')

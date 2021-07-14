"""
Create new materialized view for source data that is being used for creating
the source_metadata.csv for the EDS

Revision ID: 2021_07_13_source_data_view
Revises: 2020_12_18_level_of_geography
Create Date: 2020-07-13 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2021_07_13_source_data_view"
down_revision = "2020_12_18_level_of_geography"
branch_labels = None
depends_on = None

source_data_view = """
CREATE MATERIALIZED VIEW source_metadata AS
(
   SELECT DISTINCT
        m.id,
        mv.id as version_id,
        mv.version::text,
        mv.latest::text,
        mv.title,
        mv.description,
        mv.time_covered,
        mv.area_covered,
        mv.lowest_level_of_geography_id,
        t.title::text AS topic,
        st.title::text AS subtopic,
        t.slug AS topic_slug,
        st.slug AS subtopic_slug,
        m.slug AS measure_slug,
        dimns.dimension AS dimension,
        dimns.classification as classification,
        mds.publisher_dataset,
        mds.publisher_code,
        mds.type_of_statistic,
        mds.frequency_of_release,
        mds.type_of_data,
        mds.publisher,
        mds.publisher_type,
        mds.publisher_abbreviations,
        u.title as upload_title,
        u.description as upload_description,
        u.file_name as upload_filename,
        u.size as upload_size
    FROM
        measure_version AS mv
        INNER JOIN measure AS m ON m.id = mv.measure_id
        INNER JOIN subtopic_measure AS sm ON m.id = sm.measure_id
        INNER JOIN subtopic AS st ON st.id = sm.subtopic_id
        INNER JOIN topic AS t ON t.id = st.topic_id
        INNER JOIN (
            SELECT
                d.measure_version_id AS id,
                jsonb_agg(d.title) AS dimension,
                jsonb_agg(cls.title) AS classification
            FROM
                dimension d
                LEFT JOIN dimension_categorisation AS dcl ON dcl.dimension_guid = d.guid
                LEFT JOIN classification AS cls ON cls.id = dcl.classification_id
            GROUP BY
                d.measure_version_id) dimns ON dimns.id = mv.id
        LEFT JOIN (
            SELECT
                dsm.measure_version_id AS id,
                jsonb_agg(ds.title) AS publisher_dataset,
                jsonb_agg(ds.publisher_id) AS publisher_code,
                jsonb_agg(ts.external) AS type_of_statistic,
                jsonb_agg(fr.description) AS frequency_of_release,
                jsonb_agg(ds.type_of_data) AS type_of_data,
                jsonb_agg(org.name) AS publisher,
                jsonb_agg(org.organisation_type) AS publisher_type,
                jsonb_agg(org.abbreviations) AS publisher_abbreviations
            FROM
                data_source_in_measure_version dsm
                INNER JOIN data_source ds ON ds.id = dsm.data_source_id
                INNER JOIN type_of_statistic ts ON ts.id = ds.type_of_statistic_id
                INNER JOIN frequency_of_release fr ON fr.id = ds.frequency_of_release_id
                INNER JOIN organisation org ON org.id = ds.publisher_id
            GROUP BY
                dsm.measure_version_id) mds ON mds.id = mv.id
        INNER JOIN upload AS u ON u.measure_version_id = mv.id
    WHERE
        mv.status = 'APPROVED'
    ORDER BY
        m.id,
        mv.id,
        mv.time_covered,
        dimns.dimension
);
"""

drop_view = """
DROP MATERIALIZED VIEW IF EXISTS source_metadata;
"""


def upgrade():
    op.execute(source_data_view)


def downgrade():
    op.execute(drop_view)

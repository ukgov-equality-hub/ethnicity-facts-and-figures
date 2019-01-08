"""Populate topic, subtopic, subtopic_measure and measure table from the main page table.

Revision ID: 20181220_populate_measures
Revises: rename_uri_slug
Create Date: 2018-12-11 13:11:47.567135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20181220_populate_measures"
down_revision = "rename_uri_slug"
branch_labels = None
depends_on = None

max_measure_version_temp_table = """
CREATE TEMPORARY TABLE max_measure_version
AS
SELECT
    mv.*
FROM
    measure_version AS mv
WHERE
    mv.page_type = 'measure'
    AND mv.version = (
        SELECT
            MAX(version)
        FROM
            measure_version AS max_mv
        WHERE
            max_mv.guid = mv.guid);
"""

copy_topics = """
INSERT INTO topic (slug, title, description, additional_description)
SELECT DISTINCT
    slug, title, description, additional_description
FROM
    measure_version
WHERE
    page_type = 'topic'
"""

copy_subtopics = """
INSERT INTO subtopic (slug, title, position, topic_id)
SELECT DISTINCT
    mv_subtopic.slug, mv_subtopic.title, mv_subtopic.position, topic.id
FROM
    measure_version AS mv_subtopic
JOIN
    measure_version AS mv_topic
ON
    mv_subtopic.parent_guid = mv_topic.guid
    AND mv_subtopic.parent_version = mv_topic.version
JOIN
    topic
ON
    mv_topic.slug = topic.slug
    AND mv_topic.description = topic.description
    AND mv_topic.additional_description = topic.additional_description
WHERE
    mv_subtopic.page_type = 'subtopic'
"""

copy_measures = """
INSERT INTO measure (guid, slug, position, reference)
SELECT
    guid,
    slug,
    position,
    internal_reference
FROM
    max_measure_version;
"""

create_subtopic_measure_join_records = """
INSERT INTO subtopic_measure (subtopic_id, measure_id)
SELECT DISTINCT
    subtopic.id, measure.id
FROM
    measure_version AS mv_subtopic
JOIN
    measure_version AS mv_measure
ON
    mv_subtopic.id = mv_measure.parent_id
JOIN
    subtopic
ON
    subtopic.slug = mv_subtopic.slug
    AND mv_subtopic.page_type = 'subtopic'
JOIN
    measure
ON
    measure.guid = mv_measure.guid
    AND mv_measure.page_type = 'measure'
WHERE
    mv_subtopic.page_type = 'subtopic'
    AND mv_measure.page_type = 'measure'
"""

update_measure_versions_with_ids = """
UPDATE
    measure_version AS mv
SET
    measure_id = m.id
FROM
    (SELECT m.guid, m.id FROM measure AS m JOIN max_measure_version AS max_mv ON m.guid = max_mv.guid) AS m
WHERE
    mv.guid = m.guid
"""


def upgrade():
    # Using a temporary `guid` column on the `measure` table significantly simplifies updates/inserts and ensuring
    # data validity during the migration
    op.add_column("measure", sa.Column("guid", sa.String()))

    op.execute(max_measure_version_temp_table)
    op.execute(copy_topics)
    op.execute(copy_subtopics)
    op.execute(copy_measures)
    op.execute(create_subtopic_measure_join_records)
    op.execute(update_measure_versions_with_ids)

    op.drop_column("measure", "guid")

    # Run some basic assertions to test data validity
    conn = op.get_bind()

    count_topics_in_topic_table = conn.execute("SELECT COUNT(*) FROM topic").scalar()
    count_topics_in_page_table = conn.execute("SELECT COUNT(*) FROM measure_version WHERE page_type = 'topic'").scalar()
    assert count_topics_in_topic_table == count_topics_in_page_table, (
        f"Number of topics in monolith table ({count_topics_in_page_table}) does "
        f"not match normalised table ({count_topics_in_topic_table})"
    )

    count_subtopics_in_subtopic_table = conn.execute("SELECT COUNT(*) FROM subtopic").scalar()
    count_subtopics_in_page_table = conn.execute(
        "SELECT COUNT(*) FROM measure_version WHERE page_type = 'subtopic'"
    ).scalar()
    assert count_subtopics_in_subtopic_table == count_subtopics_in_page_table, (
        f"Number of subtopics in monolith table ({count_subtopics_in_page_table}) does "
        f"not match normalised table ({count_subtopics_in_subtopic_table})"
    )

    count_measures_in_measure_table = conn.execute("SELECT COUNT(*) FROM measure").scalar()
    count_measures_in_page_table = conn.execute("SELECT COUNT(*) FROM max_measure_version").scalar()
    assert count_measures_in_measure_table == count_measures_in_page_table, (
        f"Number of measures in monolith table ({count_measures_in_page_table}) does "
        f"not match normalised table ({count_measures_in_measure_table})"
    )

    count_subtopic_measures = conn.execute("SELECT COUNT(*) FROM subtopic_measure").scalar()
    assert count_subtopic_measures == count_measures_in_page_table, (
        f"Number of measures in monolith table ({count_measures_in_page_table}) does "
        f"not match subtopic_measure join table ({count_subtopic_measures})"
    )


def downgrade():
    op.execute("UPDATE measure_version SET measure_id = NULL WHERE page_type='measure'")
    op.execute("DELETE FROM subtopic_measure")
    op.execute("DELETE FROM subtopic")
    op.execute("DELETE FROM measure")
    op.execute("DELETE FROM topic")

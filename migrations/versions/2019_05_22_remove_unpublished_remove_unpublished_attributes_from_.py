"""Remove unpublished attributes from measure version model

Revision ID: 2019_05_22_remove_unpublished
Revises: 2019_04_18_add_topic_short_title
Create Date: 2019-05-22 08:46:50.003381

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_05_22_remove_unpublished"
down_revision = "2019_04_18_add_topic_short_title"
branch_labels = None
depends_on = None

drop_all_dashboard_helper_views = """
DROP INDEX IF EXISTS uix_latest_published_measure_versions_by_geography;
DROP INDEX IF EXISTS uix_latest_published_measure_versions;
DROP INDEX IF EXISTS uix_ethnic_groups_by_dimension;
DROP INDEX IF EXISTS uix_categorisations_by_dimension;
DROP MATERIALIZED VIEW IF EXISTS latest_published_measure_versions_by_geography;
DROP MATERIALIZED VIEW IF EXISTS ethnic_groups_by_dimension;
DROP MATERIALIZED VIEW IF EXISTS classifications_by_dimension;
DROP MATERIALIZED VIEW IF EXISTS latest_published_measure_versions;
"""

refresh_all_dashboard_helper_views = """
REFRESH MATERIALIZED VIEW CONCURRENTLY latest_published_measure_versions;
REFRESH MATERIALIZED VIEW CONCURRENTLY latest_published_measure_versions_by_geography;
REFRESH MATERIALIZED VIEW CONCURRENTLY ethnic_groups_by_dimension;
REFRESH MATERIALIZED VIEW CONCURRENTLY classifications_by_dimension;
"""

latest_published_measure_versions_view = """
CREATE MATERIALIZED VIEW latest_published_measure_versions AS
(
   SELECT
      mv.*
   FROM
      measure_version AS mv
      JOIN
         (
            SELECT
               measure_version.measure_id,
               array_to_string(MAX(string_to_array(measure_version.version, '.')), '.') AS max_approved_version
            FROM
               measure_version
            WHERE
               measure_version.status = 'APPROVED'
            GROUP BY
               measure_version.measure_id
         )
         AS max_approved_measure_versions
         ON mv.measure_id = max_approved_measure_versions.measure_id
         AND mv.version = max_approved_measure_versions.max_approved_version
);

CREATE UNIQUE INDEX uix_latest_published_measure_versions
ON latest_published_measure_versions (id);
"""

latest_published_measure_versions_by_geography_view = """
CREATE MATERIALIZED VIEW latest_published_measure_versions_by_geography AS
(
   SELECT
      topic.title AS topic_title,
      topic.slug AS topic_slug,
      subtopic.title AS subtopic_title,
      subtopic.slug AS subtopic_slug,
      subtopic.position AS subtopic_position,
      measure.slug AS measure_slug,
      measure.position AS measure_position,
      measure_version.id AS measure_version_id,
      measure_version.title AS measure_version_title,
      geography.name AS geography_name,
      geography.position AS geography_position
   FROM
      latest_published_measure_versions AS mv
      JOIN lowest_level_of_geography AS geography ON mv.lowest_level_of_geography_id = geography.name
      JOIN measure_version ON measure_version.id = mv.id
      JOIN measure ON measure.id = measure_version.measure_id
      JOIN subtopic_measure ON subtopic_measure.measure_id = measure.id
      JOIN subtopic ON subtopic.id = subtopic_measure.subtopic_id
      JOIN topic ON topic.id = subtopic.topic_id
   ORDER BY
      geography.position ASC
);

CREATE UNIQUE INDEX uix_latest_published_measure_versions_by_geography
ON latest_published_measure_versions_by_geography (measure_version_id);
"""


ethnic_groups_by_dimension_view = """
CREATE MATERIALIZED VIEW ethnic_groups_by_dimension AS
(
     SELECT
        topic.title AS topic_title,
        topic.slug AS topic_slug,
        subtopic.title AS subtopic_title,
        subtopic.slug AS subtopic_slug,
        subtopic.position AS subtopic_position,
        measure.id AS measure_id,
        measure.slug AS measure_slug,
        measure.position AS measure_position,
        latest_published_measure_versions.id AS measure_version_id,
        latest_published_measure_versions.title AS measure_version_title,
        dimension.guid AS dimension_guid,
        dimension.title AS dimension_title,
        dimension.position AS dimension_position,
        classification.title AS classification_title,
        ethnicity.value AS ethnicity_value,
        ethnicity.position AS ethnicity_position
     FROM latest_published_measure_versions
          JOIN measure ON latest_published_measure_versions.measure_id = measure.id
          JOIN subtopic_measure ON measure.id = subtopic_measure.measure_id
          JOIN subtopic ON subtopic_measure.subtopic_id = subtopic.id
          JOIN topic ON subtopic.topic_id = topic.id
          JOIN dimension ON dimension.measure_version_id = latest_published_measure_versions.id
          JOIN dimension_categorisation ON dimension.guid = dimension_categorisation.dimension_guid
          JOIN classification ON dimension_categorisation.classification_id = classification.id
          JOIN ethnicity_in_classification ON classification.id = ethnicity_in_classification.classification_id
          JOIN ethnicity ON ethnicity_in_classification.ethnicity_id = ethnicity.id
     UNION
     SELECT
        topic.title AS topic_title,
        topic.slug AS topic_slug,
        subtopic.title AS subtopic_title,
        subtopic.slug AS subtopic_slug,
        subtopic.position AS subtopic_position,
        measure.id AS measure_id,
        measure.slug AS measure_slug,
        measure.position AS measure_position,
        latest_published_measure_versions.id AS measure_version_id,
        latest_published_measure_versions.title AS measure_version_title,
        dimension.guid AS dimension_guid,
        dimension.title AS dimension_title,
        dimension.position AS dimension_position,
        classification.title AS classification_title,
        ethnicity.value AS ethnicity_value,
        ethnicity.position AS ethnicity_position
     FROM latest_published_measure_versions
          JOIN measure ON latest_published_measure_versions.measure_id = measure.id
          JOIN subtopic_measure ON measure.id = subtopic_measure.measure_id
          JOIN subtopic ON subtopic_measure.subtopic_id = subtopic.id
          JOIN topic ON subtopic.topic_id = topic.id
          JOIN dimension ON dimension.measure_version_id = latest_published_measure_versions.id
          JOIN dimension_categorisation ON dimension.guid = dimension_categorisation.dimension_guid
          JOIN classification ON dimension_categorisation.classification_id = classification.id
          JOIN parent_ethnicity_in_classification ON classification.id = parent_ethnicity_in_classification.classification_id
          JOIN ethnicity ON parent_ethnicity_in_classification.ethnicity_id = ethnicity.id
     WHERE dimension_categorisation.includes_parents
);

CREATE UNIQUE INDEX uix_ethnic_groups_by_dimension ON ethnic_groups_by_dimension (dimension_guid, ethnicity_value);
"""  # noqa


classifications_by_dimension = """
CREATE MATERIALIZED VIEW classifications_by_dimension AS
(
   SELECT
      topic.title AS topic_title,
      topic.slug AS topic_slug,
      subtopic.title AS subtopic_title,
      subtopic.slug AS subtopic_slug,
      subtopic.position AS subtopic_position,
      measure.id AS measure_id,
      measure.slug AS measure_slug,
      measure.position AS measure_position,
      latest_published_measure_versions.id AS measure_version_id,
      latest_published_measure_versions.title AS measure_version_title,
      dimension.guid AS dimension_guid,
      dimension.title AS dimension_title,
      dimension.position AS dimension_position,
      classification.id AS classification_id,
      classification.title AS classification_title,
      classification.position AS classification_position,
      dimension_categorisation.includes_parents AS includes_parents,
      dimension_categorisation.includes_all AS includes_all,
      dimension_categorisation.includes_unknown AS includes_unknown
   FROM
      latest_published_measure_versions
      JOIN measure ON latest_published_measure_versions.measure_id = measure.id
      JOIN subtopic_measure ON measure.id = subtopic_measure.measure_id
      JOIN subtopic ON subtopic_measure.subtopic_id = subtopic.id
      JOIN topic ON subtopic.topic_id = topic.id
      JOIN dimension ON dimension.measure_version_id = latest_published_measure_versions.id
      JOIN dimension_categorisation ON dimension.guid = dimension_categorisation.dimension_guid
      JOIN classification ON dimension_categorisation.classification_id = classification.id
);

CREATE UNIQUE INDEX uix_categorisations_by_dimension ON classifications_by_dimension (dimension_guid, classification_id);
"""  # noqa


def upgrade():
    op.execute(drop_all_dashboard_helper_views)

    op.drop_column("measure_version", "unpublished_at")
    op.drop_column("measure_version", "unpublished_by")

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)


def downgrade():
    op.execute(drop_all_dashboard_helper_views)

    op.add_column(
        "measure_version", sa.Column("unpublished_by", sa.VARCHAR(length=255), autoincrement=False, nullable=True)
    )
    op.add_column("measure_version", sa.Column("unpublished_at", sa.DATE(), autoincrement=False, nullable=True))

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)

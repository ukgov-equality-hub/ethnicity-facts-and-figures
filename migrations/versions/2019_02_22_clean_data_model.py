"""Clean up our data model by removing fields/indexes/etc leftover from the old one

Revision ID: 2019_02_22_clean_data_model
Revises: 2019_02_15_remove_mid_matviews
Create Date: 2019-02-22 16:40:55.560103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_02_22_clean_data_model"
down_revision = "2019_02_15_remove_mid_matviews"
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

    # drop foreign key constraints
    op.drop_constraint(op.f("measure_version_parent_id_fkey"), "measure_version", type_="foreignkey")
    op.drop_constraint(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("dimension_measure_version_id_fkey"), "dimension", type_="foreignkey")
    op.drop_constraint(op.f("upload_measure_version_id_fkey"), "upload", type_="foreignkey")

    # drop primary key constraint
    op.drop_constraint(op.f("measure_version_id_pkey"), "measure_version", type_="primary")

    # drop indexes
    op.drop_index("ix_page_type_uri", table_name="measure_version")

    # drop columns
    op.drop_column("data_source_in_measure_version", "page_version")
    op.drop_column("data_source_in_measure_version", "page_guid")
    op.drop_column("dimension", "page_id")
    op.drop_column("dimension", "page_version")
    op.drop_column("upload", "page_id")
    op.drop_column("upload", "page_version")
    op.drop_column("measure_version", "guid")
    op.drop_column("measure_version", "position")
    op.drop_column("measure_version", "parent_guid")
    op.drop_column("measure_version", "parent_version")
    op.drop_column("measure_version", "parent_id")
    op.drop_column("measure_version", "slug")
    op.drop_column("measure_version", "additional_description")
    op.drop_column("measure_version", "page_type")

    # create primary key constraint
    op.create_primary_key("measure_version_id_pkey", "measure_version", ["id"])

    # create foreign key constraints
    op.create_foreign_key(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        "measure_version",
        ["measure_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("dimension_measure_version_id_fkey"), "dimension", "measure_version", ["measure_version_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("upload_measure_version_id_fkey"), "upload", "measure_version", ["measure_version_id"], ["id"]
    )

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)


def downgrade():
    op.execute(drop_all_dashboard_helper_views)

    # drop foreign key constraints
    op.drop_constraint(op.f("upload_measure_version_id_fkey"), "upload", type_="foreignkey")
    op.drop_constraint(op.f("dimension_measure_version_id_fkey"), "dimension", type_="foreignkey")
    op.drop_constraint(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        type_="foreignkey",
    )

    # drop primary key constraint
    op.drop_constraint(op.f("measure_version_id_pkey"), "measure_version", type_="primary")

    # create columns
    op.add_column("measure_version", sa.Column("page_type", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("measure_version", sa.Column("additional_description", sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column("measure_version", sa.Column("slug", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("measure_version", sa.Column("parent_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column("measure_version", sa.Column("parent_version", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column(
        "measure_version", sa.Column("parent_guid", sa.VARCHAR(length=255), autoincrement=False, nullable=True)
    )
    op.add_column("measure_version", sa.Column("position", sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column("measure_version", sa.Column("guid", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("upload", sa.Column("page_version", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("upload", sa.Column("page_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column("dimension", sa.Column("page_version", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column("dimension", sa.Column("page_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column(
        "data_source_in_measure_version",
        sa.Column("page_guid", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.add_column(
        "data_source_in_measure_version",
        sa.Column("page_version", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )

    # NOTE: Would need to re-populate guid/version fields on `measure_version` now for the rest of the migration
    # to succeed; specifically setting up primary and foreign keys.

    # create index
    op.create_index("ix_page_type_uri", "measure_version", ["page_type", "slug"], unique=False)

    # create primary key constraint
    op.create_primary_key("measure_version_id_pkey", "measure_version", ["id", "guid", "version"])

    # create foreign key constraints
    op.create_foreign_key(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        "measure_version",
        ["measure_version_id", "page_guid", "page_version"],
        ["id", "guid", "version"],
    )
    op.create_foreign_key(
        op.f("dimension_measure_version_id_fkey"),
        "dimension",
        "measure_version",
        ["measure_version_id", "page_guid", "page_version"],
        ["id", "guid", "version"],
    )
    op.create_foreign_key(
        op.f("upload_measure_version_id_fkey"),
        "upload",
        "measure_version",
        ["measure_version_id", "page_guid", "page_version"],
        ["id", "guid", "version"],
    )

    op.execute(latest_published_measure_versions_view)
    op.execute(latest_published_measure_versions_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(classifications_by_dimension)

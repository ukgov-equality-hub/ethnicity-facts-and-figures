drop_all_dashboard_helper_views = """
    DROP INDEX IF EXISTS uix_new_latest_published_measure_versions_by_geography;
    DROP INDEX IF EXISTS uix_latest_published_measure_versions;
    DROP INDEX IF EXISTS uix_ethnic_groups_by_dimension;
    DROP INDEX IF EXISTS uix_categorisations_by_dimension;
    DROP MATERIALIZED VIEW IF EXISTS new_latest_published_measure_versions_by_geography;
    DROP MATERIALIZED VIEW IF EXISTS latest_published_measure_versions;
    DROP MATERIALIZED VIEW IF EXISTS ethnic_groups_by_dimension;
    DROP MATERIALIZED VIEW IF EXISTS categorisations_by_dimension;
"""

refresh_all_dashboard_helper_views = """
    REFRESH MATERIALIZED VIEW CONCURRENTLY latest_published_measure_versions;
    REFRESH MATERIALIZED VIEW CONCURRENTLY new_latest_published_measure_versions_by_geography;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ethnic_groups_by_dimension;
    REFRESH MATERIALIZED VIEW CONCURRENTLY categorisations_by_dimension;
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
CREATE MATERIALIZED VIEW new_latest_published_measure_versions_by_geography AS
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
      JOIN
         lowest_level_of_geography AS geography
         ON mv.lowest_level_of_geography_id = geography.name
      JOIN
         measure_version
         ON measure_version.id = mv.id
      JOIN
         measure
         ON measure.id = measure_version.measure_id
      JOIN
         subtopic_measure
         ON subtopic_measure.measure_id = measure.id
      JOIN
         subtopic
         ON subtopic.id = subtopic_measure.subtopic_id
      JOIN
         topic
         ON topic.id = subtopic.topic_id
   ORDER BY
      geography.position ASC
);

CREATE UNIQUE INDEX uix_new_latest_published_measure_versions_by_geography
ON new_latest_published_measure_versions_by_geography (measure_version_id);
"""


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

BEGIN TRANSACTION;


CREATE TEMPORARY TABLE qualityofcare_pages
AS (
    SELECT page.guid AS page_guid
    FROM page
    WHERE parent_guid = 'subtopic_qualityofcare'
);


CREATE TEMPORARY TABLE qualityofcare_charts
AS (
    SELECT dimension.chart_id
    FROM dimension
    WHERE dimension.page_id IN (
        SELECT *
        FROM qualityofcare_pages
    )
);


CREATE TEMPORARY TABLE qualityofcare_tables
AS (
    SELECT dimension.table_id
    FROM dimension
    WHERE dimension.page_id IN (
        SELECT *
        FROM qualityofcare_pages
    )
);


CREATE TEMPORARY TABLE qualityofcare_sources
AS (
    SELECT data_source.id
    FROM data_source
    JOIN data_source_in_page ON data_source_in_page.data_source_id = data_source.id
    JOIN page ON data_source_in_page.page_guid = page.guid
    AND data_source_in_page.page_version = page.version
    WHERE data_source_in_page.page_guid IN (
        SELECT *
        FROM qualityofcare_pages
    )
);


DELETE FROM dimension_chart
WHERE dimension_chart.id IN (
    SELECT *
    FROM qualityofcare_charts
);


DELETE FROM dimension_table
WHERE dimension_table.id IN (
    SELECT *
    FROM qualityofcare_tables
);


DELETE FROM data_source_in_page
WHERE data_source_in_page.data_source_id IN (
    SELECT *
    FROM qualityofcare_sources
);


DELETE FROM data_source
WHERE data_source.id IN (
    SELECT *
    FROM qualityofcare_sources
);


DELETE FROM dimension
WHERE dimension.page_id IN (
    SELECT *
    FROM qualityofcare_pages
);


DELETE FROM page
WHERE page.guid IN (
    SELECT *
    FROM qualityofcare_pages
);


DELETE FROM page
WHERE page.guid = 'subtopic_qualityofcare';


COMMIT;

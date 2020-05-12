INSERT INTO page (guid, title, uri, page_type, description, additional_description, version, created_at, parent_guid, parent_version, db_version_id)
    VALUES ('topic_population', 'British population', 'british-population', 'topic', 'Population statistics and Census data, also analysed by age, location and other factors', 'The government collects population data through the Census, which happens every 10 years, and other surveys.

Find population statistics and demographic information for different ethnic groups in England and Wales. We have included data for Scotland where it’s available.', '1.0', now(), 'homepage', '1.0', 1);

INSERT INTO page (guid, title, uri, page_type, description, version, created_at, db_version_id, parent_guid, parent_version, position)
    VALUES ('subtopic_national_and_regional_populations', 'National and regional populations', 'national-and-regional-populations', 'subtopic', 'National and regional populations', '1.0', now(), 1, 'topic_population', '1.0', 1),
           ('subtopic_demographics', 'Demographics', 'demographics', 'subtopic', 'Demographics', '1.0', now(), 1, 'topic_population', '1.0', 2);

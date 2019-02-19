UPDATE measure_version SET parent_guid = null, parent_version = null;

DELETE
FROM measure_version
WHERE page_type = 'subtopic' OR page_type = 'topic' OR page_type = 'homepage';

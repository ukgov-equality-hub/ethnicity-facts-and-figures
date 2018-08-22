INSERT INTO page (guid, title, uri, page_type, description, additional_description, version, created_at, parent_guid, parent_version, db_version_id, position)
    VALUES ('subtopic_testingspace_rdu', 'RDU testing space', 'rdu-test-space', 'subtopic', 'RDU testing space', '', '1.0', now(), 'topic_testingspace', '1.0', 1, 0),
           ('subtopic_testingspace_moj', 'MoJ testing space', 'moj-test-space', 'subtopic', 'MoJ testing space', '', '1.0', now(), 'topic_testingspace', '1.0', 1, 1),
           ('subtopic_testingspace_examples', 'Examples', 'test-space-examples', 'subtopic', 'Example measures', '', '1.0', now(), 'topic_testingspace', '1.0', 1, 2);

UPDATE page SET parent_guid = 'subtopic_testingspace_examples' WHERE parent_guid = 'subtopic_ethnicityintheuk';
UPDATE page SET parent_guid = 'subtopic_testingspace_rdu' WHERE parent_guid = 'subtopic_testmeasures';

DELETE FROM page WHERE guid IN ('subtopic_testmeasures', 'subtopic_ethnicityintheuk');

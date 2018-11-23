-- Content team have decided that for published measures without an external edit summary:
-- 1. if the page is a version 1 page, have this external edit summary: 'First published' (matches what is currently the default for new measures)
-- 2. if the page is a version 2 page, have this external edit summary: 'Updated with the latest data'
-- 3. for all other pages (which are currently all version 1.x pages), have this external edit summary: 'Minor updates for style and accuracy'

UPDATE page
SET external_edit_summary = 'First published'
WHERE version = '1.0'
AND published IS TRUE
AND (TRIM(external_edit_summary) = '' OR external_edit_summary IS NULL);

UPDATE page
SET external_edit_summary = 'Updated with the latest data'
WHERE (version = '2.0' OR version = '3.0')
AND published IS TRUE
AND (TRIM(external_edit_summary) = '' OR external_edit_summary IS NULL);

UPDATE page
SET external_edit_summary = 'Minor updates for style and accuracy'
WHERE version NOT IN ('1.0', '2.0', '3.0')
AND published IS TRUE
AND (TRIM(external_edit_summary) = '' OR external_edit_summary IS NULL);

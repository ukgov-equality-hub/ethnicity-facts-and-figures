UPDATE measure_version
SET external_edit_summary = 'First published'
WHERE version = '1.0'
AND (TRIM(external_edit_summary) = '' OR external_edit_summary IS NULL);

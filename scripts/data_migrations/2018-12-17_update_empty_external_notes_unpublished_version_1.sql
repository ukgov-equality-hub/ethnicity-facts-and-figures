UPDATE page
SET external_edit_summary = 'First published'
WHERE version = '1.0'
AND published IS FALSE
AND (TRIM(external_edit_summary) = '' OR external_edit_summary IS NULL);

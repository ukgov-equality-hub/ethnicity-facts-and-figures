UPDATE
    measure_version
SET
    status = 'APPROVED'
WHERE
    status = 'UNPUBLISH'
    or status = 'UNPUBLISHED';

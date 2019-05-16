UPDATE
    measure_version
SET
    status = 'APPROVED'
WHERE
    status = 'UNPUBLISH'
    or status = 'UNPUBLISHED';

INSERT
INTO
    build
    (id, created_at, status)
VALUES
    ('6bd13007-9e8e-4f53-bdcc-fdd3f8728611', now(), 'PENDING');

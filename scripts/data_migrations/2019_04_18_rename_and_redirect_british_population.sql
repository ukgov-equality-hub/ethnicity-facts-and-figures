UPDATE topic SET slug = 'uk-population-by-ethnicity' WHERE slug = 'british-population';
UPDATE redirect SET to_uri = REPLACE(to_uri, 'british-population/', 'uk-population-by-ethnicity/') WHERE to_uri LIKE 'british-population/%';
INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(), 'british-population', 'uk-population-by-ethnicity');

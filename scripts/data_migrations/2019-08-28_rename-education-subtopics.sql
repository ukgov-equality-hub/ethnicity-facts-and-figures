/* Rename "A-levels" to "A-levels, apprenticeships and further education" */
UPDATE subtopic
SET    slug = 'a-levels-apprenticeships-further-education',
       title='A levels, apprenticeships and further education'
WHERE  slug = 'a-levels';

/* Rename "Apprenticeships, further and higher education" to "Higher education" */
UPDATE subtopic
SET    slug = 'higher-education',
       title='Higher education'
WHERE  slug = 'apprenticeships-further-and-higher-education';

/* Move three measures from "Higher education" to "A-levels, apprenticeships and further education" */
UPDATE subtopic_measure
SET    subtopic_id = (SELECT id
                      FROM subtopic
                      WHERE slug = 'a-levels-apprenticeships-further-education'
                      )
FROM   measure
WHERE  subtopic_measure.measure_id=measure.id
        AND measure.slug IN ('further-education-participation',
                             'participation-in-apprenticeships',
                             'apprenticeship-starts');


/* Pages within
 * "A-Levels"
 * that has been moved to
 * "A-levels, apprenticeships and further education"
 */
INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/a-levels/students-aged-16-to-18-achieving-3-a-grades-or-better-at-a-level',
  'education-skills-and-training/a-levels-apprenticeships-further-education/students-aged-16-to-18-achieving-3-a-grades-or-better-at-a-level') ON CONFLICT DO NOTHING;

/* Pages within
 * "Apprenticeships, further and higher education"
 * that have moved to
 * "A-levels, apprenticeships and further education"
 */
INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/further-education-participation',
  'education-skills-and-training/a-levels-apprenticeships-further-education/further-education-participation') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/participation-in-apprenticeships',
  'education-skills-and-training/a-levels-apprenticeships-further-education/participation-in-apprenticeships') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/apprenticeship-starts',
  'education-skills-and-training/a-levels-apprenticeships-further-education/apprenticeship-starts') ON CONFLICT DO NOTHING;


/* Pages within
 * "Apprenticeships, further and higher education"
 * that have moved to
 * "Higher education"
 */
INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/entry-rates-into-higher-education',
  'education-skills-and-training/higher-education/entry-rates-into-higher-education') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/first-year-entrants-onto-undergraduate-degrees',
  'education-skills-and-training/higher-education/first-year-entrants-onto-undergraduate-degrees') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/first-year-entrants-onto-postgraduate-degrees',
  'education-skills-and-training/higher-education/first-year-entrants-onto-postgraduate-degrees') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/undergraduate-degree-results',
  'education-skills-and-training/higher-education/undergraduate-degree-results') ON CONFLICT DO NOTHING;

INSERT INTO redirect (created, from_uri, to_uri) VALUES (now(),
  'education-skills-and-training/apprenticeships-further-and-higher-education/undergraduate-degree-results',
  'education-skills-and-training/higher-education/entrants-at-higher-education-providers-with-high-medium-and-low-entry-tariffs') ON CONFLICT DO NOTHING;

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'work-pay-and-benefits'
  AND s.slug = 'employment'
  AND m.slug = 'employment'
  AND original_mv.version = '1.2'
  AND other_mv.version = '1.1';

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'education-skills-and-training'
  AND s.slug = 'after-education'
  AND m.slug = 'destinations-of-students-after-key-stage-5-usually-aged-18-years'
  AND original_mv.version = '1.2'
  AND other_mv.version = '1.0';

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'education-skills-and-training'
  AND s.slug = 'after-education'
  AND m.slug = 'destinations-of-school-pupils-after-key-stage-4-usually-aged-16-years'
  AND original_mv.version = '1.2'
  AND other_mv.version = '1.0';

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'uk-population-by-ethnicity'
  AND s.slug = 'demographics'
  AND m.slug = 'socioeconomic-status'
  AND original_mv.version = '1.1'
  AND other_mv.version = '1.0';

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'education-skills-and-training'
  AND s.slug = '11-to-16-years-old'
  AND m.slug = 'gcse-results-attainment-8-for-children-aged-14-to-16-key-stage-4'
  AND original_mv.version = '2.2'
  AND other_mv.version = '2.0';

UPDATE measure_version AS original_mv
SET update_corrects_measure_version = other_mv.id
FROM measure AS m,
     subtopic_measure AS sm,
     subtopic AS s,
     topic AS t,
     measure_version AS other_mv
WHERE original_mv.measure_id = m.id
  AND m.id = sm.measure_id
  AND sm.subtopic_id = s.id
  AND s.topic_id = t.id
  AND other_mv.measure_id = m.id
  AND t.slug = 'education-skills-and-training'
  AND s.slug = '11-to-16-years-old'
  AND m.slug = 'gcse-results-attainment-8-for-children-aged-14-to-16-key-stage-4'
  AND original_mv.version = '2.3'
  AND other_mv.version = '2.2';

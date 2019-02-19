UPDATE measure_version
SET update_corrects_data_mistake = true
FROM measure,
     subtopic_measure,
     subtopic,
     topic
WHERE measure_version.measure_id = measure.id
  AND measure.id = subtopic_measure.measure_id
  AND subtopic.id = subtopic_measure.subtopic_id
  AND topic.id = subtopic.topic_id
  AND topic.slug = 'work-pay-and-benefits'
  AND subtopic.slug = 'employment'
  AND measure.slug = 'employment'
  AND measure_version.version = '1.2';

UPDATE measure_version
SET update_corrects_data_mistake = true
FROM measure,
     subtopic_measure,
     subtopic,
     topic
WHERE measure_version.measure_id = measure.id
  AND measure.id = subtopic_measure.measure_id
  AND subtopic.id = subtopic_measure.subtopic_id
  AND topic.id = subtopic.topic_id
  AND topic.slug = 'education-skills-and-training'
  AND subtopic.slug = 'after-education'
  AND measure.slug = 'destinations-of-school-pupils-after-key-stage-4-usually-aged-16-years'
  AND measure_version.version = '1.2';

UPDATE measure_version
SET update_corrects_data_mistake = true
FROM measure,
     subtopic_measure,
     subtopic,
     topic
WHERE measure_version.measure_id = measure.id
  AND measure.id = subtopic_measure.measure_id
  AND subtopic.id = subtopic_measure.subtopic_id
  AND topic.id = subtopic.topic_id
  AND topic.slug = 'education-skills-and-training'
  AND subtopic.slug = 'after-education'
  AND measure.slug = 'destinations-of-students-after-key-stage-5-usually-aged-18-years'
  AND measure_version.version = '1.2';

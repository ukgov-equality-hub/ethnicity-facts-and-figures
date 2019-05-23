UPDATE
    measure_version
SET
    version = '3.0'
FROM
    measure,
    subtopic_measure,
    subtopic,
    topic
WHERE
    measure_version.measure_id = measure.id
    AND subtopic_measure.measure_id = measure.id
    AND subtopic.id = subtopic_measure.subtopic_id
    AND topic.id = subtopic.topic_id
    AND topic.slug = 'education-skills-and-training'
    AND subtopic.slug = '11-to-16-years-old'
    AND measure.slug = 'a-to-c-in-english-and-maths-gcse-attainment-for-children-aged-14-to-16-key-stage-4'
    AND measure_version.version = '2.5';

UPDATE
    measure_version
SET
    version = '3.0'
FROM
    measure,
    subtopic_measure,
    subtopic,
    topic
WHERE
    measure_version.measure_id = measure.id
    AND subtopic_measure.measure_id = measure.id
    AND subtopic.id = subtopic_measure.subtopic_id
    AND topic.id = subtopic.topic_id
    AND topic.slug = 'education-skills-and-training'
    AND subtopic.slug = '11-to-16-years-old'
    AND measure.slug = 'gcse-results-attainment-8-for-children-aged-14-to-16-key-stage-4'
    AND measure_version.version = '2.5';

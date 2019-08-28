UPDATE subtopic SET slug = 'a-levels-apprenticeships-further-education', title='A-levels, apprenticeships and further education' WHERE slug = 'a-levels';

UPDATE subtopic SET slug = 'higher-education', title='Higher education' WHERE slug = 'apprenticeships-further-and-higher-education';

UPDATE subtopic_measure SET subtopic_id=(SELECT id FROM subtopic WHERE slug = 'a-levels-apprenticeships-further-education') FROM measure WHERE subtopic_measure.measure_id=measure.id AND measure.slug IN ('further-education-participation', 'participation-in-apprenticeships', 'apprenticeship-starts');

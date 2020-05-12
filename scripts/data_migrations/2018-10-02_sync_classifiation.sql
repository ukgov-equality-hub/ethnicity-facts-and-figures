-- Delete the classification currently used only for "Students aged 16 to 18 achieving 3 A grades or better at A level"
-- This measure should actually be tagged with the standard DfE 18 category
DELETE from dimension_categorisation
USING classification
WHERE classification.id = dimension_categorisation.classification_id AND classification.code = '19A';
DELETE from ethnicity_in_classification
USING classification
WHERE classification.id = ethnicity_in_classification.classification_id AND classification.code = '19A';
DELETE from parent_ethnicity_in_classification
USING classification
WHERE classification.id = parent_ethnicity_in_classification.classification_id AND classification.code = '19A';
DELETE from classification
WHERE classification.code = '19A';

-- Delete unused classification "5 - Black, Indian, Pakistani and Bangladeshi, White, Other inc Mixed"
DELETE from dimension_categorisation
USING classification
WHERE classification.id = dimension_categorisation.classification_id AND classification.code = '5D';
DELETE from ethnicity_in_classification
USING classification
WHERE classification.id = ethnicity_in_classification.classification_id AND classification.code = '5D';
DELETE from parent_ethnicity_in_classification
USING classification
WHERE classification.id = parent_ethnicity_in_classification.classification_id AND classification.code = '5D';
DELETE from classification
WHERE classification.code = '5D';

-- Delete unused classification "Bangladeshi, Chinese, Indian, Pakistani, Asian other, Black, Mixed, White British, White other, Other, Arab, Gypsy/Traveller/Irish Traveller"
DELETE from dimension_categorisation
USING classification
WHERE classification.id = dimension_categorisation.classification_id AND classification.code = '11A';
DELETE from ethnicity_in_classification
USING classification
WHERE classification.id = ethnicity_in_classification.classification_id AND classification.code = '11A';
DELETE from parent_ethnicity_in_classification
USING classification
WHERE classification.id = parent_ethnicity_in_classification.classification_id AND classification.code = '11A';
DELETE from classification
WHERE classification.code = '11A';

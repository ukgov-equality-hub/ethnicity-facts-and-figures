-- Delete the classification currently used only for "Students aged 16 to 18 achieving 3 A grades or better at A level"
-- This measure should actually be tagged with the standard DfE 18 category
DELETE from dimension_categorisation
USING categorisation
WHERE categorisation.id = dimension_categorisation.categorisation_id AND categorisation.code = '19A';
DELETE from association
USING categorisation
WHERE categorisation.id = association.categorisation_id AND categorisation.code = '19A';
DELETE from parent_association
USING categorisation
WHERE categorisation.id = parent_association.categorisation_id AND categorisation.code = '19A';
DELETE from categorisation
WHERE categorisation.code = '19A';

-- Delete unused classification "5 - Black, Indian, Pakistani and Bangladeshi, White, Other inc Mixed"
DELETE from dimension_categorisation
USING categorisation
WHERE categorisation.id = dimension_categorisation.categorisation_id AND categorisation.code = '5D';
DELETE from association
USING categorisation
WHERE categorisation.id = association.categorisation_id AND categorisation.code = '5D';
DELETE from parent_association
USING categorisation
WHERE categorisation.id = parent_association.categorisation_id AND categorisation.code = '5D';
DELETE from categorisation
WHERE categorisation.code = '5D';

-- Delete unused classification "Bangladeshi, Chinese, Indian, Pakistani, Asian other, Black, Mixed, White British, White other, Other, Arab, Gypsy/Traveller/Irish Traveller"
DELETE from dimension_categorisation
USING categorisation
WHERE categorisation.id = dimension_categorisation.categorisation_id AND categorisation.code = '11A';
DELETE from association
USING categorisation
WHERE categorisation.id = association.categorisation_id AND categorisation.code = '11A';
DELETE from parent_association
USING categorisation
WHERE categorisation.id = parent_association.categorisation_id AND categorisation.code = '11A';
DELETE from categorisation
WHERE categorisation.code = '11A';


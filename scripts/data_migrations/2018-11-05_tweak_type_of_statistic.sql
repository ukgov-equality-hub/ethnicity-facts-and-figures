UPDATE type_of_statistic
SET internal = 'National Statistics (certified against the Code of Practice for Statistics)'
WHERE external = 'National Statistics';

UPDATE type_of_statistic
SET internal = 'Non-official statistics (not produced by a government department or agency)'
WHERE external = 'Non-official statistics';

"""
Update topic meta descriptions

Revision ID: 2020_05_26_update_topics
Revises: 2020_05_20_update_classification
Create Date: 2020-05-19 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_05_26_update_topics"
down_revision = "2020_05_20_update_classification"
branch_labels = None
depends_on = None

update_topics = """
UPDATE topic
SET additional_description = 'Includes data on policing, crimes, sentencing and
 prisons.'
WHERE slug = 'crime-justice-and-the-law';

UPDATE topic
SET additional_description = 'Includes data on the arts, transport and neighbourhoods.'
WHERE slug = 'culture-and-community';

UPDATE topic
SET additional_description = 'Includes data on school results, apprenticeships,
     universities and where people go after education.'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET additional_description = 'Includes data on physical and mental health,
 diet and exercise, and smoking and alcohol use.'
WHERE slug = 'health';

UPDATE topic
SET additional_description = 'Includes data on home ownership, social housing
 and homelessness.'
WHERE slug = 'housing';

UPDATE topic
SET additional_description = 'Population statistics and 2011 Census data.',
meta_description = 'UK population statistics, analysed by ethnicity, age,
     gender and other factors.'
WHERE slug = 'uk-population-by-ethnicity';

UPDATE topic
SET meta_description = 'UK population statistics, analysed by ethnicity, age,
     gender and other factors.'
WHERE slug = 'uk-population-by-ethnicity';

UPDATE topic
SET additional_description = 'Includes data on employment, unemployment,
 pay and income, and benefits.'
WHERE slug = 'work-pay-and-benefits';

UPDATE topic
SET additional_description = 'Includes data on ethnic diversity and pay in
 public services.'
WHERE slug = 'workforce-and-business';
"""

revert_topics = """
UPDATE topic
SET additional_description = 'Government departments, public services and local
 authorities collect data on policing, crimes, courts, sentencing, prisons and custody.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'crime-justice-and-the-law';

UPDATE topic
SET additional_description = 'Government departments and local authorities
 collect data on the arts, internet use, museums, libraries, volunteering,
 transport and neighbourhoods.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'culture-and-community';

UPDATE topic
SET additional_description = 'Government departments, local authorities, schools,
 colleges and universities collect data on pupil attainment, absences and
 exclusions, further and higher education, apprenticeships and where people go
 after leaving education.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET additional_description = 'Government departments, local authorities, hospitals,
 health trusts and related organisations collect data on physical and mental health,
 preventing illness, quality of care, access to treatment, and patient experiences
 and results.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'health';

UPDATE topic
SET additional_description = 'Government departments, local authorities and housing associations
 collect data on home ownership, renting, social housing, homelessness and housing conditions.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'housing';

UPDATE topic
SET additional_description = 'In the 2011 Census, 80.5% of people in England and Wales said they
 were White British, and 19.5% were from ethnic minorities. Everyone completing the Census was asked
 to choose from a [list of ethnic groups](/ethnic-groups).'
WHERE slug = 'uk-population-by-ethnicity';

UPDATE topic
SET additional_description = 'Government departments and public services collect data on ethnic
 diversity within their workforces, staff experience and pay. They also collect data on
 self-employment and running a business.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'work-pay-and-benefits';

UPDATE topic
SET additional_description = 'Government departments collect data on employment, unemployment,
 pay and income, and benefits.

Find information on outcomes for different ethnic groups.'
WHERE slug = 'workforce-and-business';
"""


def upgrade():
    op.execute(update_topics)


def downgrade():
    op.execute(revert_topics)

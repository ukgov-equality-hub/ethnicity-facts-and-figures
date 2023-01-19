"""
Update topic meta descriptions

Revision ID: 2020_06_02_update_population
Revises: 2020_05_26_update_topics
Create Date: 2020-06-02 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_06_02_update_population"
down_revision = "2020_05_26_update_topics"
branch_labels = None
depends_on = None

update_topics = """
UPDATE topic
SET additional_description = 'Includes data on school pupil results,
     apprenticeships, universities and where people go after education.'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET additional_description = 'Population statistics and Census data.

<div class="govuk-inset-text">
See the list of <a class="govuk-link" href="/ethnic-groups">ethnic groups</a> used in the 2021 Census.
</div>'
WHERE slug = 'uk-population-by-ethnicity';
"""

revert_topics = """
UPDATE topic
SET additional_description = 'Population statistics and Census data.'
WHERE slug = 'uk-population-by-ethnicity';
"""


def upgrade():
    op.execute(update_topics)


def downgrade():
    op.execute(revert_topics)

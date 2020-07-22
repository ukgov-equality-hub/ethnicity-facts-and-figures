"""
Update measure version

Revision ID: 2020_07_20_updata_topics
Revises: 2020_07_06_add_template_version
Create Date: 2020-05-19 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_07_20_updata_topics"
down_revision = "2020_07_06_add_template_version"
branch_labels = None
depends_on = None

update_topics = """
UPDATE topic
SET description = 'Schools, exclusions, further and higher education, apprenticeships after education'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET description = 'Physical and mental health, preventing illness, quality of care, patient experiences and outcomes'
WHERE slug = 'health';
"""

revert_topics = """
UPDATE topic
SET description = 'Schools, exclusions, further and higher education, apprenticeships and where people go after
 leaving education'
WHERE slug = 'education-skills-and-training';

UPDATE topic
SET description = 'Physical and mental health, preventing illness, quality of care, access to treatment,
 patient experiences and outcomes'
WHERE slug = 'health';
"""


def upgrade():
    op.execute(update_topics)


def downgrade():
    op.execute(revert_topics)

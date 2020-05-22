"""
Update topic meta descriptions

Revision ID: 2020_05_20_update_classification
Revises: 2020_05_19_update_topics
Create Date: 2020-05-19 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_05_20_update_classification"
down_revision = "2020_05_19_update_topics"
branch_labels = None
depends_on = None

update_classification = """
UPDATE classification
SET title = 'White and Other than White', long_title = 'White and Other than White'
WHERE id = '2A';
"""

revert_classification = """
UPDATE classification
SET title = 'White and Other', long_title = 'White and Other'
WHERE id = '2A';
"""


def upgrade():
    op.execute(update_classification)


def downgrade():
    op.execute(revert_classification)

"""
Rename topic

Revision ID: 2020_06_15_rename_topic
Revises: 2020_06_11_move_measure
Create Date: 2020-06-02 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_06_15_rename_topic"
down_revision = "2020_06_11_move_measure"
branch_labels = None
depends_on = None

update = """
UPDATE subtopic
SET slug='business', title='Business'
WHERE id = 10;
"""

revert = """
UPDATE subtopic
SET slug='business-and-self-employment', title='Business and self-employmen'
WHERE id = 10;
"""


def upgrade():
    op.execute(update)


def downgrade():
    op.execute(revert)

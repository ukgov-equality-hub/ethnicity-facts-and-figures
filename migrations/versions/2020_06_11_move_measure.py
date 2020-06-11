"""
Update topic meta descriptions

Revision ID: 2020_06_11_move_measure
Revises: 2020_06_02_update_population
Create Date: 2020-06-02 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_06_11_move_measure"
down_revision = "2020_06_02_update_population"
branch_labels = None
depends_on = None

update = """
UPDATE subtopic_measure
SET subtopic_id = 19
WHERE subtopic_id = 10 AND measure_id = 174;
"""

revert = """
UPDATE subtopic_measure
SET subtopic_id = 10
WHERE subtopic_id = 19 AND measure_id = 174;
"""


def upgrade():
    op.execute(update)


def downgrade():
    op.execute(revert)

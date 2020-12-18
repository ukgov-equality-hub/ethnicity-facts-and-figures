"""
Update lowest_level_of_geography

Revision ID: 2020_12_18_level_of_geography
Revises: 2020_07_20_updata_topics
Create Date: 2020-12-18 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_12_18_level_of_geography"
down_revision = "2020_07_20_updata_topics"
branch_labels = None
depends_on = None

update_geography = """
UPDATE lowest_level_of_geography
SET description = '(for example, England, England and Wales, Scotland...)'
WHERE name = 'Country';

UPDATE lowest_level_of_geography
SET description = '(for example, South West, London, North West, Wales...)'
WHERE name = 'Region';

UPDATE lowest_level_of_geography
SET description = '(for example,  County councils and unitary authorities)'
WHERE name = 'Local authority upper';

UPDATE lowest_level_of_geography
SET description = '(for example,  District councils and unitary authorities)'
WHERE name = 'Local authority lower';
"""

revert_geography = """
UPDATE lowest_level_of_geography
SET description = '(e.g. England, England and Wales, Scotland...)'
WHERE name = 'Country';

UPDATE lowest_level_of_geography
SET description = '(e.g. South West, London, North West, Wales...)'
WHERE name = 'Region';

UPDATE lowest_level_of_geography
SET description = '(e.g. County councils and unitary authorities)'
WHERE name = 'Local authority upper';

UPDATE lowest_level_of_geography
SET description = '(e.g. District councils and unitary authorities)'
WHERE name = 'Local authority lower';
"""


def upgrade():
    op.execute(update_geography)


def downgrade():
    op.execute(revert_geography)

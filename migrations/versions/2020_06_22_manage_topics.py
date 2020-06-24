"""
Add capabilities

Revision ID: 2020_06_22_manage_topics
Revises: 2020_06_15_rename_topic
Create Date: 2020-06-02 14:02:04.242855

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2020_06_22_manage_topics"
down_revision = "2020_06_15_rename_topic"
branch_labels = None
depends_on = None

update = """
UPDATE users
SET capabilities = array_append(capabilities,'manage_topics')
WHERE user_type IN ('ADMIN_USER', 'DEV_USER') and not(capabilities @> ARRAY['manage_topics'::varchar])
"""

revert = """

"""


def upgrade():
    op.execute(update)


def downgrade():
    op.execute(revert)

"""Add meta_description column to topics for SEO/open graph desc


Revision ID: 2019_04_18_meta_desc
Revises: 2019_04_18_add_topic_short_title
Create Date: 2019-04-18 13:56:13.692874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_04_18_meta_desc"
down_revision = "2019_04_18_add_topic_short_title"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("topic", sa.Column("meta_description", sa.TEXT(), nullable=True))


def downgrade():
    op.drop_column("topic", "meta_description")

"""
Adds "long_title" column to the categorisation table.
This is because we want to show short titles internally in the Publisher, but full longer titles in the public-facing
dashboards.

Revision ID: 2018_09_25_add_long_title
Revises: 2018_10_15_index_page_type_uri
Create Date: 2018-09-24 15:15:35.190282

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_09_25_add_long_title"
down_revision = "2018_10_15_index_page_type_uri"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("categorisation", sa.Column("long_title", sa.String(length=255), nullable=True))

    op.get_bind()
    op.execute(
        """
            UPDATE categorisation SET long_title = title;
        """
    )


def downgrade():
    op.drop_column("categorisation", "long_title")

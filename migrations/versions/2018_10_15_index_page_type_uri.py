"""add composite index for page uri and version

Revision ID: 2018_10_15_index_page_type_uri
Revises: 2018_10_05_chart_table_fkeys
Create Date: 2018-10-15 11:58:37.004443

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_10_15_index_page_type_uri"
down_revision = "2018_10_05_chart_table_fkeys"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_page_type_uri", "page", ["page_type", "uri"], unique=False)


def downgrade():
    op.drop_index("ix_page_type_uri", table_name="page")

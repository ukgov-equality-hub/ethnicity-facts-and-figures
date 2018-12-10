"""Remove duplicated foreign key on data_source_in_page

Revision ID: 2018_12_03_remove_duplicate_fkey
Revises: 2018_12_03_fix_migrations
Create Date: 2018-11-05 09:05:59.517656

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_12_03_remove_duplicate_fkey"
down_revision = "2018_12_03_fix_migrations"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    res = conn.execute(
        "SELECT constraint_name "
        "FROM information_schema.table_constraints "
        "WHERE table_name='data_source_in_page' AND constraint_name = 'data_source_in_page_data_source_id_fkey1';"
    )

    if len(res.fetchall()) > 0:
        op.drop_constraint("data_source_in_page_data_source_id_fkey1", "data_source_in_page", type_="foreignkey")


def downgrade():
    op.create_foreign_key(
        "data_source_in_page_data_source_id_fkey1", "data_source_in_page", "data_source", ["data_source_id"], ["id"]
    )

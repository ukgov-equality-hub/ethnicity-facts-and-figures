"""empty message

Revision ID: 18a2aea8ea85
Revises: 20181214_published_unpublished
Create Date: 2018-12-20 10:52:50.641092

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_uri_slug'
down_revision = '20181214_published_unpublished'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('measure_version', 'uri', new_column_name='slug')
    op.alter_column('measure', 'uri', new_column_name='slug')
    op.alter_column('topic', 'uri', new_column_name='slug')
    op.alter_column('subtopic', 'uri', new_column_name='slug')


def downgrade():
    op.alter_column('measure_version', 'slug', new_column_name='uri')
    op.alter_column('measure', 'slug', new_column_name='uri')
    op.alter_column('topic', 'slug', new_column_name='uri')
    op.alter_column('subtopic', 'slug', new_column_name='uri')


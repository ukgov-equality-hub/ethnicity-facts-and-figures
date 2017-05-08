"""empty message

Revision ID: eaff27489153
Revises: fe159ce13e78
Create Date: 2017-05-08 10:49:53.035245

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eaff27489153'
down_revision = 'fe159ce13e78'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('audit', 'action', existing_type=sa.String(255), type_=sa.Text())


def downgrade():
    op.alter_column('audit', 'action', existing_type=sa.Text(), type_=sa.String(255))

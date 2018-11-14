"""fix data source purpose length

Revision ID: 2018_11_12_data_source_purpose
Revises: 2018_10_31_refactor_data_sources
Create Date: 2018-11-12 22:01:27.458373

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_11_12_data_source_purpose"
down_revision = "2018_10_31_refactor_data_sources"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("data_source", "frequency_of_release_other", type_=sa.VARCHAR(length=255), existing_type=sa.TEXT())
    op.alter_column("data_source", "purpose", type_=sa.TEXT(), existing_type=sa.VARCHAR(length=255))


def downgrade():
    op.alter_column("data_source", "purpose", type_=sa.VARCHAR(length=255), existing_type=sa.TEXT())
    op.alter_column("data_source", "frequency_of_release_other", type_=sa.TEXT(), existing_type=sa.VARCHAR(length=255))

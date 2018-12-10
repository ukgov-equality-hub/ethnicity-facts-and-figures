"""fix migrations by incorporating outstanding changes

Revision ID: 2018_12_03_fix_migrations
Revises: 2018_11_28_drop_contact_details
Create Date: 2018-12-03 10:51:52.822365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_12_03_fix_migrations"
down_revision = "2018_11_28_drop_contact_details"
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "data_source_frequency_of_release_id_fkey",
        "data_source",
        "frequency_of_release",
        ["frequency_of_release_id"],
        ["id"],
    )
    op.alter_column("dimension_chart", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column("dimension_table", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column(
        "ethnicity_in_classification", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False
    )
    op.alter_column("ethnicity_in_classification", "ethnicity_id", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column(
        "parent_ethnicity_in_classification", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=False
    )
    op.alter_column("parent_ethnicity_in_classification", "ethnicity_id", existing_type=sa.INTEGER(), nullable=False)


def downgrade():
    op.alter_column("parent_ethnicity_in_classification", "ethnicity_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "parent_ethnicity_in_classification", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True
    )
    op.alter_column("ethnicity_in_classification", "ethnicity_id", existing_type=sa.INTEGER(), nullable=True)
    op.alter_column(
        "ethnicity_in_classification", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True
    )
    op.alter_column("dimension_table", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column("dimension_chart", "classification_id", existing_type=sa.VARCHAR(length=255), nullable=True)
    op.drop_constraint("data_source_frequency_of_release_id_fkey", "data_source", type_="foreignkey")

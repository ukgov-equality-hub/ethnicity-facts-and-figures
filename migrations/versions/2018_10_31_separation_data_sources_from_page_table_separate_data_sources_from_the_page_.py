"""Separate data sources from the page table

Revision ID: 2018_10_31_refactor_data_sources
Revises: 2018_10_15_index_page_type_uri
Create Date: 2018-11-05 09:05:59.517656

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2018_10_31_refactor_data_sources"
down_revision = "2018_10_05_chart_table_fkeys"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "data_source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "type_of_data",
            postgresql.ARRAY(postgresql.ENUM(name="type_of_data_types", create_type=False)),
            nullable=True,
        ),
        sa.Column("type_of_statistic_id", sa.Integer(), nullable=True),
        sa.Column("publisher_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=255), nullable=True),
        sa.Column("publication_date", sa.String(length=255), nullable=True),
        sa.Column("note_on_corrections_or_updates", sa.TEXT(), nullable=True),
        sa.Column("frequency_of_release_id", sa.Integer(), nullable=True),
        sa.Column("frequency_of_release_other", sa.TEXT(), nullable=True),
        sa.Column("purpose", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["publisher_id"], ["organisation.id"]),
        sa.ForeignKeyConstraint(["type_of_statistic_id"], ["type_of_statistic.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "data_source_in_page",
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("page_guid", sa.String(length=255), nullable=False),
        sa.Column("page_version", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["data_source_id"], ["data_source.id"]),
        sa.ForeignKeyConstraint(["page_guid", "page_version"], ["page.guid", "page.version"]),
        sa.PrimaryKeyConstraint(
            "data_source_id", "page_guid", "page_version", name="data_source_id_page_guid_version_pk"
        ),
    )


def downgrade():
    op.drop_table("data_source_in_page")
    op.drop_table("data_source")

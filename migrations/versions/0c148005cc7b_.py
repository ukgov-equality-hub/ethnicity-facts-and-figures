"""empty message

Revision ID: 0c148005cc7b
Revises: e722179fb7a8
Create Date: 2017-11-23 11:53:01.401864

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0c148005cc7b"
down_revision = "e722179fb7a8"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind()

    op.drop_constraint("db_dimension_measure_id_version_fkey", "db_dimension", type_="foreignkey")
    op.drop_constraint("db_dimension_pkey", "db_dimension", type_="primary")

    op.drop_constraint("db_upload_page_id_version_fkey", "db_upload", type_="foreignkey")
    op.drop_constraint("db_upload_pkey", "db_upload", type_="primary")

    op.drop_constraint("db_page_parent_guid_version_fkey", "db_page", type_="foreignkey")
    op.drop_constraint("db_page_guid_version_pkey", "db_page", type_="primary")

    op.alter_column("db_dimension", "measure_id", new_column_name="page_id", existing_type=sa.String)
    op.alter_column("db_dimension", "measure_version", new_column_name="page_version", existing_type=sa.String)

    op.rename_table("db_page", "page")
    op.rename_table("db_dimension", "dimension")
    op.rename_table("db_upload", "upload")

    op.create_primary_key("page_guid_version_pkey", "page", ["guid", "version"])
    op.create_unique_constraint("uix_page_guid_version", "page", ["guid", "version"])
    op.create_foreign_key(
        "page_parent_guid_version_fkey", "page", "page", ["parent_guid", "parent_version"], ["guid", "version"]
    )

    op.create_primary_key("upload_pkey", "upload", ["guid"])
    op.create_foreign_key(
        "upload_page_id_version_fkey", "upload", "page", ["page_id", "page_version"], ["guid", "version"]
    )

    op.create_primary_key("dimension_pkey", "dimension", ["guid"])
    op.create_foreign_key(
        "dimension_page_id_version_fkey", "dimension", "page", ["page_id", "page_version"], ["guid", "version"]
    )


def downgrade():
    op.get_bind()

    op.drop_constraint("dimension_page_id_version_fkey", "dimension", type_="foreignkey")
    op.drop_constraint("dimension_pkey", "dimension", type_="primary")

    op.drop_constraint("upload_page_id_version_fkey", "upload", type_="foreignkey")
    op.drop_constraint("upload_pkey", "upload", type_="primary")

    op.drop_constraint("page_parent_guid_version_fkey", "page", type_="foreignkey")
    op.drop_constraint("page_guid_version_pkey", "page", type_="primary")
    op.drop_constraint("uix_page_guid_version", "page", type_="unique")

    op.alter_column("dimension", "page_id", new_column_name="measure_id", existing_type=sa.String)
    op.alter_column("dimension", "page_version", new_column_name="measure_version", existing_type=sa.String)

    op.rename_table("page", "db_page")
    op.rename_table("dimension", "db_dimension")
    op.rename_table("upload", "db_upload")

    op.create_primary_key("db_page_guid_version_pkey", "db_page", ["guid", "version"])
    op.create_foreign_key(
        "db_page_parent_guid_version_fkey", "db_page", "db_page", ["parent_guid", "parent_version"], ["guid", "version"]
    )

    op.create_primary_key("db_upload_pkey", "db_upload", ["guid"])
    op.create_foreign_key(
        "db_upload_page_id_version_fkey", "db_upload", "db_page", ["page_id", "page_version"], ["guid", "version"]
    )

    op.create_primary_key("db_dimension_pkey", "db_dimension", ["guid"])
    op.create_foreign_key(
        "db_dimension_measure_id_version_fkey",
        "db_dimension",
        "db_page",
        ["measure_id", "measure_version"],
        ["guid", "version"],
    )

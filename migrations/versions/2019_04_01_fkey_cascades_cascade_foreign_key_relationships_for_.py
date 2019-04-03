"""Cascade foreign key relationships for deleting measure versions

Revision ID: 2019_04_01_fkey_cascades
Revises: 2019_03_25_remove_title
Create Date: 2019-04-01 15:43:15.024950

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2019_04_01_fkey_cascades"
down_revision = "2019_03_25_remove_title"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("data_source_frequency_of_release_id_fkey", "data_source", type_="foreignkey")
    op.drop_constraint("data_source_type_of_statistic_id_fkey", "data_source", type_="foreignkey")
    op.drop_constraint("data_source_publisher_id_fkey", "data_source", type_="foreignkey")
    op.create_foreign_key(
        "data_source_type_of_statistic_id_fkey",
        "data_source",
        "type_of_statistic",
        ["type_of_statistic_id"],
        ["id"],
        ondelete="restrict",
    )
    op.create_foreign_key(
        "data_source_publisher_id_fkey", "data_source", "organisation", ["publisher_id"], ["id"], ondelete="restrict"
    )
    op.create_foreign_key(
        "data_source_frequency_of_release_id_fkey",
        "data_source",
        "frequency_of_release",
        ["frequency_of_release_id"],
        ["id"],
        ondelete="restrict",
    )
    op.drop_constraint("data_source_in_page_data_source_id_fkey", "data_source_in_measure_version", type_="foreignkey")
    op.drop_constraint(
        "data_source_in_measure_version_measure_version_id_fkey", "data_source_in_measure_version", type_="foreignkey"
    )
    op.create_foreign_key(
        "data_source_in_page_data_source_id_fkey",
        "data_source_in_measure_version",
        "data_source",
        ["data_source_id"],
        ["id"],
        ondelete="restrict",
    )
    op.create_foreign_key(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        "measure_version",
        ["measure_version_id"],
        ["id"],
        ondelete="cascade",
    )
    op.drop_constraint("dimension_measure_version_id_fkey", "dimension", type_="foreignkey")
    op.create_foreign_key(
        op.f("dimension_measure_version_id_fkey"),
        "dimension",
        "measure_version",
        ["measure_version_id"],
        ["id"],
        ondelete="cascade",
    )
    op.drop_constraint("dimension_categorisation_classification_fkey", "dimension_categorisation", type_="foreignkey")
    op.drop_constraint("dimension_dimension_categorisation_fkey", "dimension_categorisation", type_="foreignkey")
    op.create_foreign_key(
        op.f("dimension_categorisation_classification_id_fkey"),
        "dimension_categorisation",
        "classification",
        ["classification_id"],
        ["id"],
        ondelete="restrict",
    )
    op.create_foreign_key(
        op.f("dimension_categorisation_dimension_guid_fkey"),
        "dimension_categorisation",
        "dimension",
        ["dimension_guid"],
        ["guid"],
        ondelete="cascade",
    )
    op.drop_constraint("measure_version_measure_id_fkey", "measure_version", type_="foreignkey")
    op.drop_constraint("page_lowest_level_of_geography_fkey", "measure_version", type_="foreignkey")
    op.create_foreign_key(
        op.f("measure_version_measure_id_fkey"),
        "measure_version",
        "measure",
        ["measure_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        op.f("measure_version_lowest_level_of_geography_id_fkey"),
        "measure_version",
        "lowest_level_of_geography",
        ["lowest_level_of_geography_id"],
        ["name"],
        ondelete="restrict",
    )
    op.drop_constraint("subtopic_measure_subtopic_id_fkey", "subtopic_measure", type_="foreignkey")
    op.drop_constraint("subtopic_measure_measure_id_fkey", "subtopic_measure", type_="foreignkey")
    op.create_foreign_key(
        op.f("subtopic_measure_subtopic_id_fkey"),
        "subtopic_measure",
        "subtopic",
        ["subtopic_id"],
        ["id"],
        ondelete="restrict",
    )
    op.create_foreign_key(
        op.f("subtopic_measure_measure_id_fkey"),
        "subtopic_measure",
        "measure",
        ["measure_id"],
        ["id"],
        ondelete="cascade",
    )
    op.drop_constraint("upload_measure_version_id_fkey", "upload", type_="foreignkey")
    op.create_foreign_key(
        op.f("upload_measure_version_id_fkey"),
        "upload",
        "measure_version",
        ["measure_version_id"],
        ["id"],
        ondelete="cascade",
    )
    op.drop_constraint("user_page_user_id_fkey", "user_measure", type_="foreignkey")
    op.drop_constraint("user_page_measure_id_fkey", "user_measure", type_="foreignkey")
    op.create_foreign_key(
        op.f("user_measure_user_id_fkey"), "user_measure", "users", ["user_id"], ["id"], ondelete="cascade"
    )
    op.create_foreign_key(
        op.f("user_measure_measure_id_fkey"), "user_measure", "measure", ["measure_id"], ["id"], ondelete="cascade"
    )


def downgrade():
    op.drop_constraint(op.f("user_measure_measure_id_fkey"), "user_measure", type_="foreignkey")
    op.drop_constraint(op.f("user_measure_user_id_fkey"), "user_measure", type_="foreignkey")
    op.create_foreign_key("user_page_measure_id_fkey", "user_measure", "measure", ["measure_id"], ["id"])
    op.create_foreign_key("user_page_user_id_fkey", "user_measure", "users", ["user_id"], ["id"])
    op.drop_constraint(op.f("upload_measure_version_id_fkey"), "upload", type_="foreignkey")
    op.create_foreign_key("upload_measure_version_id_fkey", "upload", "measure_version", ["measure_version_id"], ["id"])
    op.drop_constraint(op.f("subtopic_measure_measure_id_fkey"), "subtopic_measure", type_="foreignkey")
    op.drop_constraint(op.f("subtopic_measure_subtopic_id_fkey"), "subtopic_measure", type_="foreignkey")
    op.create_foreign_key("subtopic_measure_measure_id_fkey", "subtopic_measure", "measure", ["measure_id"], ["id"])
    op.create_foreign_key("subtopic_measure_subtopic_id_fkey", "subtopic_measure", "subtopic", ["subtopic_id"], ["id"])
    op.drop_constraint(op.f("measure_version_lowest_level_of_geography_id_fkey"), "measure_version", type_="foreignkey")
    op.drop_constraint(op.f("measure_version_measure_id_fkey"), "measure_version", type_="foreignkey")
    op.create_foreign_key(
        "page_lowest_level_of_geography_fkey",
        "measure_version",
        "lowest_level_of_geography",
        ["lowest_level_of_geography_id"],
        ["name"],
    )
    op.create_foreign_key("measure_version_measure_id_fkey", "measure_version", "measure", ["measure_id"], ["id"])
    op.drop_constraint(
        op.f("dimension_categorisation_dimension_guid_fkey"), "dimension_categorisation", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("dimension_categorisation_classification_id_fkey"), "dimension_categorisation", type_="foreignkey"
    )
    op.create_foreign_key(
        "dimension_dimension_categorisation_fkey", "dimension_categorisation", "dimension", ["dimension_guid"], ["guid"]
    )
    op.create_foreign_key(
        "dimension_categorisation_classification_fkey",
        "dimension_categorisation",
        "classification",
        ["classification_id"],
        ["id"],
    )
    op.drop_constraint(op.f("dimension_measure_version_id_fkey"), "dimension", type_="foreignkey")
    op.create_foreign_key(
        "dimension_measure_version_id_fkey", "dimension", "measure_version", ["measure_version_id"], ["id"]
    )
    op.drop_constraint(
        op.f("data_source_in_measure_version_measure_version_id_fkey"),
        "data_source_in_measure_version",
        type_="foreignkey",
    )
    op.drop_constraint("data_source_in_page_data_source_id_fkey", "data_source_in_measure_version", type_="foreignkey")
    op.create_foreign_key(
        "data_source_in_measure_version_measure_version_id_fkey",
        "data_source_in_measure_version",
        "measure_version",
        ["measure_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        "data_source_in_page_data_source_id_fkey",
        "data_source_in_measure_version",
        "data_source",
        ["data_source_id"],
        ["id"],
    )
    op.drop_constraint("data_source_frequency_of_release_id_fkey", "data_source", type_="foreignkey")
    op.drop_constraint("data_source_publisher_id_fkey", "data_source", type_="foreignkey")
    op.drop_constraint("data_source_type_of_statistic_id_fkey", "data_source", type_="foreignkey")
    op.create_foreign_key("data_source_publisher_id_fkey", "data_source", "organisation", ["publisher_id"], ["id"])
    op.create_foreign_key(
        "data_source_type_of_statistic_id_fkey", "data_source", "type_of_statistic", ["type_of_statistic_id"], ["id"]
    )
    op.create_foreign_key(
        "data_source_frequency_of_release_id_fkey",
        "data_source",
        "frequency_of_release",
        ["frequency_of_release_id"],
        ["id"],
    )

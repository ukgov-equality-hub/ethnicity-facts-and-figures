from application.data.tables import TableObjectDataBuilder
from tests.test_data.table_convert import (
    v1_settings_simple,
    v1_settings_ethnicity_as_rows,
    v1_settings_ethnicity_as_columns,
)


def test_v1_to_v2_upgrade_migrates_basics(dictionary_lookup):
    # GIVEN
    #
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    #
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    #
    assert v2_settings["version"] == "2.0"
    assert v2_settings["tableValues"]["table_title"] == v1_settings["tableOptions"]["table_title"]


def test_v1_to_v2_upgrade_migrates_value_columns(dictionary_lookup):
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # value columns should copy straight across
    assert v2_settings["tableValues"]["table_column_1"] == v1_settings["tableOptions"]["table_column_1"]
    assert v2_settings["tableValues"]["table_column_2"] == v1_settings["tableOptions"]["table_column_2"]
    assert v2_settings["tableValues"]["table_column_3"] == v1_settings["tableOptions"]["table_column_3"]
    assert v2_settings["tableValues"]["table_column_4"] == v1_settings["tableOptions"]["table_column_4"]
    assert v2_settings["tableValues"]["table_column_5"] == v1_settings["tableOptions"]["table_column_5"]

    assert v2_settings["tableValues"]["table_column_1_name"] == (
        v1_settings["tableOptions"]["table_column_1_name"] or None
    )
    assert v2_settings["tableValues"]["table_column_2_name"] == (
        v1_settings["tableOptions"]["table_column_2_name"] or None
    )
    assert v2_settings["tableValues"]["table_column_3_name"] == (
        v1_settings["tableOptions"]["table_column_3_name"] or None
    )
    assert v2_settings["tableValues"]["table_column_4_name"] == (
        v1_settings["tableOptions"]["table_column_4_name"] or None
    )
    assert v2_settings["tableValues"]["table_column_5_name"] == (
        v1_settings["tableOptions"]["table_column_5_name"] or None
    )


def test_v1_to_v2_upgrade_migrates_data_for_simple_tables(dictionary_lookup):
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # data should contain values for each
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Average population per month" in v2_settings["data"][0]
    assert "Average number of self harm incidents per month" in v2_settings["data"][0]


def test_v1_to_v2_upgrade_returns_blank_dict_for_simple_options(dictionary_lookup):
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {}


def test_v1_to_v2_upgrade_returns_dict_with_settings_for_ethnicity_as_row_table(dictionary_lookup):
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_ethnicity_as_rows()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {"data_style": "ethnicity_as_row", "selection": "Time", "order": "[None]"}


def test_v1_to_v2_upgrade_returns_dict_with_settings_for_ethnicity_as_columns_table(dictionary_lookup):
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_ethnicity_as_columns()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {
        "data_style": "ethnicity_as_column",
        "selection": "Year (12 months ending March)",
        "order": "[None]",
    }


def test_v1_to_v2_upgrade_migrates_data_for_tables_grouped_by_row(dictionary_lookup):
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_ethnicity_as_rows()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # data should contain values for each column necessary to setup this table using v2
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Time" in v2_settings["data"][0]


def test_v1_to_v2_upgrade_migrates_data_for_tables_grouped_by_column(dictionary_lookup):
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_ethnicity_as_columns()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings, dictionary_lookup)

    # THEN
    # data should contain values for each column necessary to setup this table using v2
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Year (12 months ending March)" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Average population per month" in v2_settings["data"][0]
    assert "Average number of self harm incidents per month" in v2_settings["data"][0]

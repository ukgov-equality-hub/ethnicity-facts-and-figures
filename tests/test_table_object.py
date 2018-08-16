import pytest

from application.cms.data_utils import TableObjectDataBuilder
from application.static_site.table_factory import (
    build_simple_table,
    build_grouped_table,
    index_of_column,
    unique_maintain_order,
    ColumnsMissingException,
    build_table_from_json,
)
from application.static_site.models import SimpleTable, GroupedTable, DataRow, DataGroup
from tests.test_data.table_convert import (
    v1_settings_simple,
    v1_settings_ethnicity_as_rows,
    v1_settings_ethnicity_as_columns,
)

header = "Simple test table"
subtitle = "Simple subtitle"
footer = "Simple footer"
caption = "Ethnicity"
data_values = [
    ["Ethnicity", "Parent", "Percentage", "Total", "Standard Order", "Percentage Order", "Total Order"],
    ["White", "White", "100", "1000", 600, 100, 1000],
    ["Asian", "BAME", "50", "100", 100, 65, 150],
    ["Black", "BAME", "11", "60", 200, 11, 60],
    ["Mixed", "BAME", "110", "60", 300, 110, 60],
    ["Other", "BAME", "78", "35", 1000, 78, 35],
]


def test_simple_table_builder_does_return_simple_table():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )
    assert simple_table is not None
    assert isinstance(simple_table, SimpleTable)


def test_simple_table_builder_data_is_data_rows():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    assert 0 < len(simple_table.data)
    assert isinstance(simple_table.data[0], DataRow)


def test_simple_table_builder_data_rows_contain_correct_data():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    # THEN
    # Asian row should take values from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == "Asian"][0]

    assert "Asian" == asian_row.category
    assert ["50", "100"] == asian_row.values


def test_simple_table_builder_data_rows_contain_values_as_default_sort():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    # THEN
    # Asian row should come from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == "Asian"][0]

    assert "Asian" == asian_row.category
    assert ["50", "100"] == asian_row.sort_values


def test_simple_table_builder_data_rows_contain_sort_values_if_specified():
    # GIVEN
    # default values with specified sort_columns
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]
    sort_columns = ["Percentage Order", "Total Order"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=sort_columns,
        data_table=data_values,
    )

    # THEN
    # Asian row should come from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == "Asian"][0]

    assert "Asian" == asian_row.category
    assert [65, 150] == asian_row.sort_values


def test_simple_table_builder_table_columns_property_is_the_column_captions():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    assert value_column_captions == simple_table.columns


def test_simple_table_builder_data_rows_default_relationships_are_false():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    # THEN
    # test rows for appropriate default parent-child info
    for row in simple_table.data:
        assert "parent" not in row.relationships
        assert not row.relationships["is_parent"]
        assert not row.relationships["is_child"]


def test_simple_table_builder_data_rows_relationships_contain_parent_child_information():
    # GIVEN
    # default values with a specified parent
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]
    parent_column_name = "Parent"

    # WHEN
    # we build a simple table with parent-child
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=parent_column_name,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    # THEN
    # test the first two rows for appropriate data
    white_row = simple_table.data[0]
    assert "White" == white_row.relationships["parent"]
    assert white_row.relationships["is_parent"] is True
    assert white_row.relationships["is_child"] is False

    black_row = simple_table.data[1]
    assert "BAME" == black_row.relationships["parent"]
    assert black_row.relationships["is_parent"] is False
    assert black_row.relationships["is_child"] is True


def test_simple_table_builder_converts_to_dict_and_json():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )
    simple_table_dict = simple_table.to_dict()
    simple_table_json = simple_table.to_json()

    # THEN
    # dict objects and json strings are created
    assert simple_table_dict is not None
    assert isinstance(simple_table_dict, dict)

    assert simple_table_json is not None
    assert isinstance(simple_table_json, str)


def test_index_of_column_returns_column_index():
    # GIVEN
    columns = ["a", "b", "c", "d"]

    assert 0 == index_of_column(columns, "a")
    assert 3 == index_of_column(columns, "d")


def test_index_of_column_returns_none_when_not_found():
    # GIVEN
    columns = ["a", "b", "c", "d"]

    assert index_of_column(columns, "e") is None


def test_exception_raised_if_category_column_does_not_exist():
    # GIVEN
    # a category column that does not exist in the data
    invalid_category_column = "This column does not exist"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # THEN
    # an error should be raised
    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table with the invalid category
        simple_table = build_simple_table(
            header,
            subtitle,
            footer,
            category_caption=caption,
            category_column_name=invalid_category_column,
            value_column_names=value_columns,
            value_column_captions=value_column_captions,
            parent_column_name=None,
            order_column_name=None,
            sort_column_names=None,
            data_table=data_values,
        )


def test_exception_raised_if_no_value_columns_exist():
    # GIVEN
    # two values column that don't exist in the data
    category_column = "Ethnicity"
    value_columns = ["Fish", "Chips"]
    value_column_captions = ["fish", "chips"]

    # THEN
    # an error should be raised
    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table which will have no value columns
        simple_table = build_simple_table(
            header,
            subtitle,
            footer,
            category_caption=caption,
            category_column_name=category_column,
            value_column_names=value_columns,
            value_column_captions=value_column_captions,
            parent_column_name=None,
            order_column_name=None,
            sort_column_names=None,
            data_table=data_values,
        )


def test_exception_not_raised_if_at_least_one_value_column_exists():
    # GIVEN
    # a one value column that exists in the data and one that doesn't
    category_column = "Ethnicity"
    value_columns = ["Fish", "Percentage"]
    value_column_captions = ["fish", "%age"]

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(
        header,
        subtitle,
        footer,
        category_caption=caption,
        category_column_name=category_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=data_values,
    )

    # THEN
    # we expect no exception
    # and we expect our simple table to have one column of data
    row = simple_table.data[0]
    assert len(row.values) == 1


grouped_header = "Grouped test table"
grouped_subtitle = "Grouped table subtitle"
grouped_footer = "Grouped table footer"
grouped_caption = "Ethnicity"
grouped_data_values = [
    ["Ethnicity", "Gender", "Parent", "Percentage", "Total", "Standard Order", "Percentage Order", "Total Order"],
    ["White", "Male", "White", "100", "1000", 600, 100, 1000],
    ["Asian", "Male", "BAME", "50", "100", 100, 49, 99],
    ["Black", "Male", "BAME", "11", "60", 200, 11, 60],
    ["Mixed", "Male", "BAME", "110", "60", 300, 110, 60],
    ["Other", "Male", "BAME", "78", "35", 1000, 78, 35],
    ["White", "Female", "White", "97", "978", 600, 97, 978],
    ["Asian", "Female", "BAME", "53", "102", 100, 52, 101],
    ["Black", "Female", "BAME", "14", "62", 200, 14, 62],
    ["Mixed", "Female", "BAME", "90", "62", 300, 90, 62],
    ["Other", "Female", "BAME", "81", "37", 1000, 81, 37],
]


def test_grouped_table_builder_does_return_grouped_table():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )
    assert grouped_table is not None
    assert isinstance(grouped_table, GroupedTable)


def test_grouped_table_builder_data_is_data_rows():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    assert len(grouped_table.data) is not 0
    assert isinstance(grouped_table.data[0], DataRow)


def test_grouped_table_builder_data_rows_contain_correct_data():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    #
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 50, 100]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 53, 102
    asian_row = [row for row in grouped_table.data if row.category == "Asian"][0]
    assert "Asian" == asian_row.category
    assert ["50", "100", "53", "102"] == asian_row.values


def test_grouped_table_builder_data_rows_contain_values_as_default_sort():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 49, 99]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101
    asian_row = [row for row in grouped_table.data if row.category == "Asian"][0]
    assert "Asian" == asian_row.category
    assert ["50", "100", "53", "102"] == asian_row.sort_values


def test_grouped_table_builder_data_rows_contain_sort_values_if_specified():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]
    sort_columns = ["Percentage Order", "Total Order"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=sort_columns,
        data_table=grouped_data_values,
    )

    # THEN
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 49, 99]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101
    asian_row = [row for row in grouped_table.data if row.category == "Asian"][0]
    assert "Asian" == asian_row.category
    assert [49, 99, 52, 101] == asian_row.sort_values


def test_grouped_table_builder_data_rows_default_relationships_are_false():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # test rows for appropriate default parent-child info
    for row in grouped_table.data:
        assert "parent" not in row.relationships
        assert not row.relationships["is_parent"]
        assert not row.relationships["is_child"]


def test_grouped_table_builder_data_rows_relationships_contain_parent_child_information():
    # GIVEN
    # default values plus a parent column
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]
    parent_column_name = "Parent"

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=parent_column_name,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # test the first two rows for appropriate data
    white_row = grouped_table.data[0]
    assert "White" == white_row.relationships["parent"]
    assert white_row.relationships["is_parent"] is True
    assert white_row.relationships["is_child"] is False

    black_row = grouped_table.data[1]
    assert "BAME" == black_row.relationships["parent"]
    assert black_row.relationships["is_parent"] is False
    assert black_row.relationships["is_child"] is True


def test_grouped_table_builder_groups_is_data_groups():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    assert len(grouped_table.groups) is not 0
    assert isinstance(grouped_table.groups[0], DataGroup)


def test_grouped_table_builder_data_groups_contain_correct_group_values():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    group_names = [group.group for group in grouped_table.groups]
    assert ["Male", "Female"] == group_names


def test_grouped_table_builder_data_groups_contain_correct_data():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 53, 102
    female_group = [group for group in grouped_table.groups if group.group == "Female"][0]
    asian_female = [item for item in female_group.data if item.category == "Asian"][0]
    assert ["53", "102"] == asian_female.values


def test_grouped_table_builder_data_groups_contain_values_as_default_sort():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101
    female_group = [group for group in grouped_table.groups if group.group == "Female"][0]
    asian_female = [item for item in female_group.data if item.category == "Asian"][0]
    assert ["53", "102"] == asian_female.sort_values


def test_grouped_table_builder_data_groups_default_relationships_are_false():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    # THEN
    # test rows for appropriate default parent-child info
    for group in grouped_table.groups:
        for item in group.data:
            assert "parent" not in item.relationships
            assert not item.relationships["is_parent"]
            assert not item.relationships["is_child"]


def test_grouped_table_builder_converts_to_dict_and_json():
    # GIVEN
    # default values plus a parent column
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a dictionary for a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )
    grouped_table_dict = grouped_table.to_dict()
    grouped_table_json = grouped_table.to_json()

    # THEN
    # dict objects and json strings are created
    assert grouped_table_dict is not None
    assert isinstance(grouped_table_dict, dict)

    assert grouped_table_json is not None
    assert isinstance(grouped_table_json, str)


def test_grouped_table_builder_table_columns_property_is_the_column_captions():
    # GIVEN
    # default values
    category_column = "Ethnicity"
    group_column = "Gender"
    value_columns = ["Percentage", "Total"]
    value_column_captions = ["%age", "count"]

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption=grouped_caption,
        category_column_name=category_column,
        group_column_name=group_column,
        value_column_names=value_columns,
        value_column_captions=value_column_captions,
        parent_column_name=None,
        order_column_name=None,
        sort_column_names=None,
        data_table=grouped_data_values,
    )

    assert value_column_captions == grouped_table.columns


def test_unique_maintain_order_returns_unique_values():
    # GIVEN
    items = ["x", "x", "a", "b"]

    # WHEN
    unique_list = unique_maintain_order(items)

    # THEN
    items_as_set = set(items)
    assert len(items_as_set) == len(unique_list)


def test_unique_maintain_order_retains_order():
    # GIVEN
    items = ["x", "x", "a", "b", "x", "y", "b"]

    # WHEN
    unique_list = unique_maintain_order(items)

    # THEN
    assert ["x", "a", "b", "y"] == unique_list


def simple_table_object():
    return build_simple_table(
        header,
        subtitle,
        footer,
        category_caption="Ethnicity",
        category_column_name="Ethnicity",
        value_column_names=["Percentage", "Total"],
        value_column_captions=["%age", "count"],
        parent_column_name="Parent",
        order_column_name="Standard Order",
        sort_column_names=["Percentage Order", "Total Order"],
        data_table=data_values,
    )


def simple_table_json():
    return simple_table_object().to_json()


def grouped_table_object():
    return build_grouped_table(
        grouped_header,
        grouped_subtitle,
        grouped_footer,
        category_caption="Ethnicity",
        category_column_name="Ethnicity",
        group_column_name="Gender",
        value_column_names=["Percentage", "Total"],
        value_column_captions=["%age", "count"],
        parent_column_name="Parent",
        order_column_name="Standard Order",
        sort_column_names=["Percentage Order", "Total Order"],
        data_table=grouped_data_values,
    )


def grouped_table_json():
    return grouped_table_object().to_json()


def test_table_from_json_returns_correct_type_of_table():
    # GIVEN
    simple_json = simple_table_json()
    grouped_json = grouped_table_json()

    # WHEN
    simple = build_table_from_json(simple_json)
    grouped = build_table_from_json(grouped_json)

    # THEN
    assert simple is not None
    assert grouped is not None
    assert isinstance(simple, SimpleTable)
    assert isinstance(grouped, GroupedTable)


def test_table_from_json_returns_correct_headers_footers_and_subtitles():
    # GIVEN
    simple = simple_table_object()
    grouped = grouped_table_object()
    simple_json = simple.to_json()
    grouped_json = grouped.to_json()

    # WHEN
    simple_restored = build_table_from_json(simple_json)
    grouped_restored = build_table_from_json(grouped_json)

    # THEN
    assert simple.header == simple_restored.header
    assert grouped.header == grouped_restored.header

    assert simple.subtitle == simple_restored.subtitle
    assert grouped.subtitle == grouped_restored.subtitle

    assert simple.footer == simple_restored.footer
    assert grouped.footer == grouped_restored.footer


def test_simple_table_from_json_returns_correct_top_level_fields():
    # GIVEN
    simple = simple_table_object()
    simple_json = simple.to_json()

    # WHEN
    simple_restored = build_table_from_json(simple_json)

    # THEN
    assert simple.category == simple_restored.category
    assert simple.type == simple_restored.type
    assert simple.columns == simple_restored.columns
    assert simple.parent_child == simple_restored.parent_child
    assert simple.category_caption == simple_restored.category_caption


def test_grouped_table_from_json_returns_correct_top_level_fields():
    # GIVEN
    grouped = grouped_table_object()
    grouped_json = grouped.to_json()

    # WHEN
    grouped_restored = build_table_from_json(grouped_json)

    # THEN
    assert grouped.category == grouped_restored.category
    assert grouped.type == grouped_restored.type
    assert grouped.columns == grouped_restored.columns
    assert grouped.parent_child == grouped_restored.parent_child
    assert grouped.category_caption == grouped_restored.category_caption

    assert grouped.group_columns == grouped_restored.group_columns
    assert grouped.group_column == grouped_restored.group_column


def test_simple_table_from_json_returns_correct_data():
    # GIVEN
    simple = simple_table_object()
    simple_json = simple.to_json()

    # WHEN
    simple_restored = build_table_from_json(simple_json)

    # THEN
    assert data_lists_equal(simple.data, simple_restored.data)


def test_grouped_table_from_json_returns_correct_data():
    # GIVEN
    grouped = grouped_table_object()
    grouped_json = grouped.to_json()

    # WHEN
    grouped_restored = build_table_from_json(grouped_json)

    # THEN
    assert data_lists_equal(grouped.data, grouped_restored.data)


def test_grouped_table_from_json_returns_correct_group_columns():
    # GIVEN
    grouped = grouped_table_object()
    grouped_json = grouped.to_json()

    # WHEN
    grouped_restored = build_table_from_json(grouped_json)

    # THEN
    assert grouped.group_columns == grouped_restored.group_columns


def test_grouped_table_from_json_returns_correct_groups():
    # GIVEN
    grouped = grouped_table_object()
    grouped_json = grouped.to_json()

    # WHEN
    grouped_restored = build_table_from_json(grouped_json)

    # THEN
    assert data_group_lists_equal(grouped.groups, grouped_restored.groups)


def data_points_equal(point_1, point_2):
    """
    Compare 2 data rows
    :type point_1: DataRow
    :type point_2: DataRow
    """
    if (
        point_1.category != point_2.category
        or point_1.values != point_2.values
        or point_1.order != point_2.order
        or point_1.relationships != point_2.relationships
        or point_1.sort_values != point_2.sort_values
    ):
        return False
    return True


def data_lists_equal(list_1, list_2):
    if len(list_1) != len(list_2):
        return False

    sorted_1 = sorted(list_1, key=lambda k: k.category)
    sorted_2 = sorted(list_2, key=lambda k: k.category)
    for i in range(len(sorted_1)):
        if not data_points_equal(sorted_1[i], sorted_2[i]):
            return False
    return True


def data_group_lists_equal(list_1, list_2):
    if len(list_1) != len(list_2):
        return False

    sorted_1 = sorted(list_1, key=lambda k: k.group)
    sorted_2 = sorted(list_2, key=lambda k: k.group)
    for i in range(len(sorted_1)):
        if not data_groups_equal(sorted_1[i], sorted_2[i]):
            return False
    return True


def data_groups_equal(group_1, group_2):
    if group_1.group != group_2.group:
        return False
    return data_lists_equal(group_1.data, group_2.data)


def test_v1_to_v2_upgrade_migrates_basics():
    # GIVEN
    #
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    #
    from application.cms.data_utils import TableObjectDataBuilder

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    #
    assert v2_settings["version"] == "2.0"
    assert v2_settings["tableValues"]["table_title"] == v1_settings["tableOptions"]["table_title"]


def test_v1_to_v2_upgrade_migrates_value_columns():
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    from application.cms.data_utils import TableObjectDataBuilder

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # value columns should copy straight across
    assert v2_settings["tableValues"]["table_column_1"] == v1_settings["tableOptions"]["table_column_1"]
    assert v2_settings["tableValues"]["table_column_2"] == v1_settings["tableOptions"]["table_column_2"]
    assert v2_settings["tableValues"]["table_column_3"] == v1_settings["tableOptions"]["table_column_3"]
    assert v2_settings["tableValues"]["table_column_4"] == v1_settings["tableOptions"]["table_column_4"]
    assert v2_settings["tableValues"]["table_column_5"] == v1_settings["tableOptions"]["table_column_5"]

    assert v2_settings["tableValues"]["table_column_1_name"] == v1_settings["tableOptions"]["table_column_1_name"]
    assert v2_settings["tableValues"]["table_column_2_name"] == v1_settings["tableOptions"]["table_column_2_name"]
    assert v2_settings["tableValues"]["table_column_3_name"] == v1_settings["tableOptions"]["table_column_3_name"]
    assert v2_settings["tableValues"]["table_column_4_name"] == v1_settings["tableOptions"]["table_column_4_name"]
    assert v2_settings["tableValues"]["table_column_5_name"] == v1_settings["tableOptions"]["table_column_5_name"]


def test_v1_to_v2_upgrade_migrates_data_for_simple_tables():
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    from application.cms.data_utils import TableObjectDataBuilder

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # data should contain values for each
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Average population per month" in v2_settings["data"][0]
    assert "Average number of self harm incidents per month" in v2_settings["data"][0]


def test_v1_to_v2_upgrade_returns_blank_dict_for_simple_options():
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_simple()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {}


def test_v1_to_v2_upgrade_returns_dict_with_settings_for_ethnicity_as_row_table():
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_ethnicity_as_rows()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {"data_style": "ethnicity_as_row", "selection": "Time", "order": "[None]"}


def test_v1_to_v2_upgrade_returns_dict_with_settings_for_ethnicity_as_columns_table():
    # GIVEN
    # simple v1 table and settings
    v1_table_and_settings = v1_settings_ethnicity_as_columns()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade
    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # v2 tableOptions for a simple table should be an empty dict
    assert v2_settings["tableOptions"] == {
        "data_style": "ethnicity_as_column",
        "selection": "Year (12 months ending March)",
        "order": "[None]",
    }


def test_v1_to_v2_upgrade_migrates_data_for_tables_grouped_by_row():
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_ethnicity_as_rows()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # data should contain values for each column necessary to setup this table using v2
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Time" in v2_settings["data"][0]


def test_v1_to_v2_upgrade_migrates_data_for_tables_grouped_by_column():
    # GIVEN
    # a v1 table + settings object
    v1_table_and_settings = v1_settings_ethnicity_as_columns()
    v1_table = v1_table_and_settings["table"]
    v1_settings = v1_table_and_settings["table_source_data"]

    # WHEN
    # we upgrade

    v2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(v1_table, v1_settings)

    # THEN
    # data should contain values for each column necessary to setup this table using v2
    assert "data" in v2_settings
    assert len(v2_settings["data"]) == len(v1_settings["data"])
    assert "Ethnicity" in v2_settings["data"][0]
    assert "Year (12 months ending March)" in v2_settings["data"][0]
    assert "Value" in v2_settings["data"][0]
    assert "Average population per month" in v2_settings["data"][0]
    assert "Average number of self harm incidents per month" in v2_settings["data"][0]

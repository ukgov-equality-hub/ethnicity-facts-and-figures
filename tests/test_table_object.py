import pytest

from application.static_site.table_factory import build_simple_table, build_grouped_table, \
    index_of_column, unique_maintain_order, ColumnsMissingException, GroupDataMissingException
from application.static_site.models import SimpleTable, GroupedTable, DataRow

header = 'Simple test table'
subtitle = 'Simple subtitle'
footer = 'Simple footer'
caption = 'Ethnicity'
data_values = [['Ethnicity', 'Parent', 'Percentage', 'Total', 'Standard Order', 'Percentage Order', 'Total Order'],
               ['White', 'White', '100', '1000', 600, 100, 1000],
               ['Asian', 'BAME', '50', '100', 100, 65, 150],
               ['Black', 'BAME', '11', '60', 200, 11, 60],
               ['Mixed', 'BAME', '110', '60', 300, 110, 60],
               ['Other', 'BAME', '78', '35', 1000, 78, 35]
               ]


def test_simple_table_builder_does_return_simple_table():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)
    assert simple_table is not None
    assert isinstance(simple_table, SimpleTable)


def test_simple_table_builder_data_is_data_rows():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    assert 0 < len(simple_table.data)
    assert isinstance(simple_table.data[0], DataRow)


def test_simple_table_builder_data_rows_contain_correct_data():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    # THEN
    # Asian row should take values from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == 'Asian'][0]

    assert 'Asian' == asian_row.category
    assert ['50', '100'] == asian_row.values


def test_simple_table_builder_data_rows_contain_values_as_default_sort():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    # THEN
    # Asian row should come from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == 'Asian'][0]

    assert 'Asian' == asian_row.category
    assert ['50', '100'] == asian_row.sort_values


def test_simple_table_builder_data_rows_contain_sort_values_if_specified():
    # GIVEN
    # default values with specified sort_columns
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']
    sort_columns = ['Percentage Order', 'Total Order']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=sort_columns,
                                      data_table=data_values)

    # THEN
    # Asian row should come from
    # ['Asian', 'BAME', '50', '100', 100, 65, 150]
    asian_row = [row for row in simple_table.data if row.category == 'Asian'][0]

    assert 'Asian' == asian_row.category
    assert [65, 150] == asian_row.sort_values


def test_simple_table_builder_table_columns_property_is_the_column_captions():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    assert value_column_captions == simple_table.columns


def test_simple_table_builder_data_rows_default_relationships_are_false():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    # THEN
    # test rows for appropriate default parent-child info
    for row in simple_table.data:
        assert 'parent' not in row.relationships
        assert not row.relationships['is_parent']
        assert not row.relationships['is_child']


def test_simple_table_builder_data_rows_relationships_contain_parent_child_information():
    # GIVEN
    # default values with a specified parent
    category_column = 'Ethnicity'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']
    parent_column_name = 'Parent'

    # WHEN
    # we build a simple table with parent-child
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=parent_column_name,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    # THEN
    # test the first two rows for appropriate data
    white_row = simple_table.data[0]
    assert 'White' == white_row.relationships['parent']
    assert white_row.relationships['is_parent'] is True
    assert white_row.relationships['is_child'] is False

    black_row = simple_table.data[1]
    assert 'BAME' == black_row.relationships['parent']
    assert black_row.relationships['is_parent'] is False
    assert black_row.relationships['is_child'] is True


def test_index_of_column_returns_column_index():
    # GIVEN
    columns = ['a', 'b', 'c', 'd']

    assert 0 == index_of_column(columns, 'a')
    assert 3 == index_of_column(columns, 'd')


def test_index_of_column_returns_none_when_not_found():
    # GIVEN
    columns = ['a', 'b', 'c', 'd']

    assert index_of_column(columns, 'e') is None


def test_exception_raised_if_category_column_does_not_exist():
    # GIVEN
    # a category column that does not exist in the data
    invalid_category_column = 'This column does not exist'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # THEN
    # an error should be raised
    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table with the invalid category
        simple_table = build_simple_table(header, subtitle, footer,
                                          category_caption=caption,
                                          category_column_name=invalid_category_column,
                                          value_column_names=value_columns,
                                          value_column_captions=value_column_captions,
                                          parent_column_name=None,
                                          order_column_name=None,
                                          sort_column_names=None,
                                          data_table=data_values)


def test_exception_raised_if_no_value_columns_exist():
    # GIVEN
    # two values column that don't exist in the data
    category_column = 'Ethnicity'
    value_columns = ['Fish', 'Chips']
    value_column_captions = ['fish', 'chips']

    # THEN
    # an error should be raised
    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table which will have no value columns
        simple_table = build_simple_table(header, subtitle, footer,
                                          category_caption=caption,
                                          category_column_name=category_column,
                                          value_column_names=value_columns,
                                          value_column_captions=value_column_captions,
                                          parent_column_name=None,
                                          order_column_name=None,
                                          sort_column_names=None,
                                          data_table=data_values)


def test_exception_not_raised_if_at_least_one_value_column_exists():
    # GIVEN
    # a one value column that exists in the data and one that doesn't
    category_column = 'Ethnicity'
    value_columns = ['Fish', 'Percentage']
    value_column_captions = ['fish', '%age']

    # WHEN
    # we build a simple table
    simple_table = build_simple_table(header, subtitle, footer,
                                      category_caption=caption,
                                      category_column_name=category_column,
                                      value_column_names=value_columns,
                                      value_column_captions=value_column_captions,
                                      parent_column_name=None,
                                      order_column_name=None,
                                      sort_column_names=None,
                                      data_table=data_values)

    # THEN
    # we expect no exception
    # and we expect our simple table to have one column of data
    row = simple_table.data[0]
    assert len(row.values) == 1


grouped_header = 'Grouped test table'
grouped_subtitle = 'Grouped table subtitle'
grouped_footer = 'Grouped table footer'
grouped_caption = 'Ethnicity'
grouped_data_values = \
    [['Ethnicity', 'Gender', 'Parent', 'Percentage', 'Total', 'Standard Order', 'Percentage Order', 'Total Order'],
     ['White', 'Male', 'White', '100', '1000', 600, 100, 1000],
     ['Asian', 'Male', 'BAME', '50', '100', 100, 49, 99],
     ['Black', 'Male', 'BAME', '11', '60', 200, 11, 60],
     ['Mixed', 'Male', 'BAME', '110', '60', 300, 110, 60],
     ['Other', 'Male', 'BAME', '78', '35', 1000, 78, 35],
     ['White', 'Female', 'White', '97', '978', 600, 97, 978],
     ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101],
     ['Black', 'Female', 'BAME', '14', '62', 200, 14, 62],
     ['Mixed', 'Female', 'BAME', '90', '62', 300, 90, 62],
     ['Other', 'Female', 'BAME', '81', '37', 1000, 81, 37]]


def test_grouped_table_builder_does_return_grouped_table():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)
    assert grouped_table is not None
    assert isinstance(grouped_table, GroupedTable)


def test_grouped_table_builder_data_is_data_rows():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    assert len(grouped_table.data) is not 0
    assert isinstance(grouped_table.data[0], DataRow)


def test_grouped_table_builder_data_rows_contain_correct_data():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    # THEN
    #
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 50, 100]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 53, 102
    asian_row = [row for row in grouped_table.data if row.category == 'Asian'][0]
    assert 'Asian' == asian_row.category
    assert ['50', '100', '53', '102'] == asian_row.values


def test_grouped_table_builder_data_rows_contain_values_as_default_sort():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    # THEN
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 49, 99]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101
    asian_row = [row for row in grouped_table.data if row.category == 'Asian'][0]
    assert 'Asian' == asian_row.category
    assert ['50', '100', '53', '102'] == asian_row.sort_values


def test_grouped_table_builder_data_rows_contain_sort_values_if_specified():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']
    sort_columns = ['Percentage Order', 'Total Order']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=sort_columns,
                                        data_table=grouped_data_values)

    # THEN
    # ['Asian', 'Male', 'BAME', '50', '100', 100, 49, 99]
    # ['Asian', 'Female', 'BAME', '53', '102', 100, 52, 101
    asian_row = [row for row in grouped_table.data if row.category == 'Asian'][0]
    assert 'Asian' == asian_row.category
    assert [49, 99, 52, 101] == asian_row.sort_values


def test_grouped_table_builder_data_rows_default_relationships_are_false():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    # THEN
    # test rows for appropriate default parent-child info
    for row in grouped_table.data:
        assert 'parent' not in row.relationships
        assert not row.relationships['is_parent']
        assert not row.relationships['is_child']


def test_grouped_table_builder_data_rows_relationships_contain_parent_child_information():
    # GIVEN
    # default values plus a parent column
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']
    parent_column_name = 'Parent'

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=parent_column_name,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    # THEN
    # test the first two rows for appropriate data
    white_row = grouped_table.data[0]
    assert 'White' == white_row.relationships['parent']
    assert white_row.relationships['is_parent'] is True
    assert white_row.relationships['is_child'] is False

    black_row = grouped_table.data[1]
    assert 'BAME' == black_row.relationships['parent']
    assert black_row.relationships['is_parent'] is False
    assert black_row.relationships['is_child'] is True


def test_grouped_table_builder_table_columns_property_is_the_column_captions():
    # GIVEN
    # default values
    category_column = 'Ethnicity'
    group_column = 'Gender'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    # WHEN
    # we build a grouped table
    grouped_table = build_grouped_table(grouped_header, grouped_subtitle, grouped_footer,
                                        category_caption=grouped_caption,
                                        category_column_name=category_column,
                                        group_column_name=group_column,
                                        value_column_names=value_columns,
                                        value_column_captions=value_column_captions,
                                        parent_column_name=None,
                                        order_column_name=None,
                                        sort_column_names=None,
                                        data_table=grouped_data_values)

    assert value_column_captions == grouped_table.columns


def test_unique_maintain_order_returns_unique_values():
    # GIVEN
    items = ['x', 'x', 'a', 'b']

    # WHEN
    unique_list = unique_maintain_order(items)

    # THEN
    items_as_set = set(items)
    assert len(items_as_set) == len(unique_list)


def test_unique_maintain_order_retains_order():
    # GIVEN
    items = ['x', 'x', 'a', 'b', 'x', 'y', 'b']

    # WHEN
    unique_list = unique_maintain_order(items)

    # THEN
    assert ['x', 'a', 'b', 'y'] == unique_list

import pytest

from application.static_site.table_factory import build_simple_table, index_of_column, ColumnsMissingException
from application.static_site.models import SimpleTable, DataRow

header = 'Simple test table'
subtitle = 'Simple subtitle'
footer = 'Simple footer'
caption = 'Ethnicity'
data_values = [['Ethnicity','Parent', 'Percentage', 'Total', 'Standard Order', 'Percentage Order', 'Total Order'],
               ['White',    'White',  '100',        '1000',     600,             100,               1000],
               ['Asian',    'BAME',   '50',         '100',      100,             50,                100],
               ['Black',    'BAME',   '11',         '60',       200,             11,                60],
               ['Mixed',    'BAME',   '110',        '60',       300,             110,               60],
               ['Other',    'BAME',   '78',         '35',       1000,            78,                35]
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
                                      value_column_captions= value_column_captions,
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


def test_simple_table_builder_default_relationships_are_false():
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
        assert not 'parent' in row.relationships
        assert not row.relationships['is_parent']
        assert not row.relationships['is_child']


def test_simple_table_builder_relationships_contain_parent_child_information():
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
    assert True == white_row.relationships['is_parent']
    assert False == white_row.relationships['is_child']

    black_row = simple_table.data[1]
    assert 'BAME' == black_row.relationships['parent']
    assert False == black_row.relationships['is_parent']
    assert True == black_row.relationships['is_child']


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
    category_column = 'This column does not exist'
    value_columns = ['Percentage', 'Total']
    value_column_captions = ['%age', 'count']

    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table expect the exception
        simple_table = build_simple_table(header, subtitle, footer,
                                          category_caption=caption,
                                          category_column_name=category_column,
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

    with pytest.raises(ColumnsMissingException):
        # WHEN
        # we build a simple table expect the exception
        simple_table = build_simple_table(header, subtitle, footer,
                                          category_caption=caption,
                                          category_column_name=category_column,
                                          value_column_names=value_columns,
                                          value_column_captions=value_column_captions,
                                          parent_column_name=None,
                                          order_column_name=None,
                                          sort_column_names=None,
                                          data_table=data_values)


def test_exception_raised_if_not_raised_if_at_least_one_value_column_exists():
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

from application.static_site.models import SimpleTable, GroupedTable, DataRow


class ColumnsMissingException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def build_simple_table(header, subtitle, footer,
                       category_caption, category_column_name,
                       value_column_captions, value_column_names, parent_column_name,
                       order_column_name, sort_column_names,
                       data_table):
    header_row = data_table[0]
    data = data_table[1:]

    # get correct indices to extract data from table for mandatory columns
    category_column_index = index_of_column(header_row, category_column_name)
    value_column_indices = [index_of_column(header_row, value_column_name) for value_column_name in value_column_names]
    value_column_indices = [v for v in value_column_indices if v is not None]

    # check mandatory columns exist
    if category_column_index is None or len(value_column_indices) == 0:
        raise ColumnsMissingException()

    # get correct indices for optional columns
    parent_column_index = index_of_column(header_row, parent_column_name)
    order_column_index = index_of_column(header_row, order_column_name)

    if sort_column_names:
        sort_column_indices = [index_of_column(header_row, sort_column_name) for sort_column_name in sort_column_names]
        if len(sort_column_indices) != len(value_column_indices):
            sort_column_indices = []
            print('Could not match sort_indices to columns in table ', header)
    else:
        sort_column_indices = []

    # build the data object
    data_rows = build_simple_data_rows(data, category_column_index, order_column_index, parent_column_index,
                                       sort_column_indices, value_column_indices)

    # return a simple table
    is_parent_child = True if parent_column_index else False
    return SimpleTable(header, subtitle, footer,
                       parent_child=is_parent_child,
                       category=category_column_name,
                       category_caption=category_caption,
                       columns=value_column_captions,
                       data=data_rows)


def build_simple_data_rows(data, category_column_index, order_column_index, parent_column_index,
                           sort_column_indices, value_column_indices):
    data_rows = []
    for row in data:
        category_value = row[category_column_index]
        values = [row[v] for v in value_column_indices]
        parent_value = row[parent_column_index] if parent_column_index else None
        order_value = row[order_column_index] if order_column_index else None
        sort_column_values = [row[s] for s in sort_column_indices]
        data_row = DataRow(category_value, values, parent_value, order_value, sort_column_values)
        data_rows = data_rows + [data_row]
    return data_rows


def build_grouped_table(header, subtitle, footer,
                        category_caption, category_column_name, group_column_name,
                        value_column_captions, value_column_names, parent_column_name,
                        order_column_name, sort_column_names,
                        data_table):

    header_row = data_table[0]
    data = data_table[1:]

    # get correct indices to extract data from table for mandatory columns
    category_column_index = index_of_column(header_row, category_column_name)
    value_column_indices = [index_of_column(header_row, value_column_name) for value_column_name in value_column_names]
    value_column_indices = [v for v in value_column_indices if v is not None]

    # check mandatory columns exist
    if category_column_index is None or len(value_column_indices) == 0:
        raise ColumnsMissingException()

    # get correct indices for optional columns
    parent_column_index = index_of_column(header_row, parent_column_name)
    order_column_index = index_of_column(header_row, order_column_name)

    # build the data object
    data_rows = []
    for row in data:
        new_data_row = DataRow('category', ['1', '2'], '', 1, [1,2])
        data_rows = data_rows + [new_data_row]

    return GroupedTable(header, subtitle, footer,
                        parent_child=False,
                        category=category_column_name, category_caption=category_caption,
                        columns=value_column_captions,
                        data=data_rows,
                        groups=[],
                        group_columns=[])


def index_of_column(headers, column):
    try:
        return headers.index(column)
    except ValueError as e:
        return None

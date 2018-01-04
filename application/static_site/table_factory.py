import json
from application.static_site.models import SimpleTable, GroupedTable, DataRow, DataGroup


class ColumnsMissingException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class GroupDataMissingException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def build_table_from_json(json_str):
    as_dict = json.loads(json_str)
    return build_table_from_dict(as_dict)


def build_table_from_dict(table_dict):
    header = table_dict['header']
    subtitle = table_dict['subtitle']
    footer = table_dict['footer']

    category = table_dict['category']
    category_caption = table_dict['category_caption']
    parent_child = table_dict['parent_child']
    columns = table_dict['columns']

    if table_dict['type'] == 'grouped':
        group_column = table_dict['group_column']
        group_columns = table_dict['group_columns']
        return GroupedTable(header, subtitle, footer,
                            parent_child=parent_child,
                            category=category,
                            category_caption=category_caption,
                            columns=columns,
                            data=build_data_rows_from_list(table_dict['data']),
                            groups=[],
                            group_columns=group_columns, group_column=group_column)
    else:
        return SimpleTable(header, subtitle, footer, parent_child=parent_child,
                           category=category,
                           category_caption=category_caption,
                           columns=columns,
                           data=build_data_rows_from_list(table_dict['data']))


def build_data_rows_from_list(row_dicts):
    return [build_data_row_from_dict(row_dict) for row_dict in row_dicts]


def build_data_row_from_dict(row_dict):
    parent = row_dict['relationships']['parent']
    return DataRow(row_dict['category'], row_dict['values'],
                   parent, row_dict['order'], row_dict['sort_values'])


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
    sort_column_indices = get_sort_column_indices(header, header_row, sort_column_names, value_column_indices)

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
    group_column_index = index_of_column(header_row, group_column_name)
    value_column_indices = [index_of_column(header_row, value_column_name) for value_column_name in value_column_names]
    value_column_indices = [v for v in value_column_indices if v is not None]

    # check mandatory columns exist
    if category_column_index is None or group_column_index is None or len(value_column_indices) == 0:
        raise ColumnsMissingException()

    # get correct indices for optional columns
    parent_column_index = index_of_column(header_row, parent_column_name)
    order_column_index = index_of_column(header_row, order_column_name)
    sort_column_indices = get_sort_column_indices(header, header_row, sort_column_names, value_column_indices)

    # build the data object
    data_rows = build_grouped_data_rows(data, category_column_index, group_column_index, order_column_index,
                                        parent_column_index, sort_column_indices, value_column_indices)

    group_columns = unique_maintain_order([row[group_column_index] for row in data])
    data_groups = build_grouped_data_groups(data, category_column_index, group_column_index, order_column_index,
                                            parent_column_index, sort_column_indices, value_column_indices)

    is_parent_child = True if parent_column_index else False
    return GroupedTable(header, subtitle, footer,
                        parent_child=is_parent_child,
                        category=category_column_name, category_caption=category_caption,
                        columns=value_column_captions,
                        data=data_rows,
                        groups=data_groups,
                        group_columns=group_columns,
                        group_column=group_column_name)


def get_sort_column_indices(header, header_row, sort_column_names, value_column_indices):
    if sort_column_names:
        sort_column_indices = [index_of_column(header_row, sort_column_name) for sort_column_name in sort_column_names]
        if len(sort_column_indices) != len(value_column_indices):
            sort_column_indices = []
            print('Could not match sort_indices to columns in table ', header)
    else:
        sort_column_indices = []
    return sort_column_indices


def build_grouped_data_rows(data, category_column_index, group_column_index, order_column_index, parent_column_index,
                            sort_column_indices, value_column_indices):
    data_rows = []

    categories = unique_maintain_order([r[category_column_index] for r in data])
    groups = unique_maintain_order([r[group_column_index] for r in data])

    for category in categories:
        category_value = category
        category_data = [row for row in data if row[category_column_index] == category]

        first_row = category_data[0]
        parent_value = first_row[parent_column_index] if parent_column_index else None
        order_value = first_row[order_column_index] if order_column_index else None

        values = []
        sort_column_values = []
        for group in groups:
            # NOTE This should throw an appropriate error if no crosstab data can be found
            group_row = [row for row in category_data if row[group_column_index] == group][0]
            group_values = [group_row[v] for v in value_column_indices]
            group_sort_values = [group_row[s] for s in sort_column_indices]

            values += group_values
            sort_column_values += group_sort_values

        data_row = DataRow(category_value, values, parent_value, order_value, sort_column_values)
        data_rows = data_rows + [data_row]
    return data_rows


def build_grouped_data_groups(data, category_column_index, group_column_index, order_column_index, parent_column_index,
                              sort_column_indices, value_column_indices):
    data_groups = []

    categories = unique_maintain_order([r[category_column_index] for r in data])
    groups = unique_maintain_order([r[group_column_index] for r in data])

    for group in groups:
        group_data = [row for row in data if row[group_column_index] == group]

        group_items = []
        for category in categories:
            # NOTE This should throw an appropriate error if no crosstab data can be found
            category_row = [row for row in group_data if row[category_column_index] == category][0]
            category_values = [category_row[v] for v in value_column_indices]

            parent_value = category_row[parent_column_index] if parent_column_index else None
            order_value = category_row[order_column_index] if order_column_index else None
            category_sort_values = [category_row[s] for s in sort_column_indices]

            data_row = DataRow(category, category_values, parent_value, order_value, category_sort_values)
            group_items += [data_row]

        data_groups += [DataGroup(group, group_items)]

    return data_groups


def index_of_column(headers, column):
    try:
        return headers.index(column)
    except ValueError as e:
        return None


def unique_maintain_order(list_items):
    new_list = []
    new_set = set([])
    for item in list_items:
        if item not in new_set:
            new_list = new_list + [item]
            new_set.add(item)
    return new_list

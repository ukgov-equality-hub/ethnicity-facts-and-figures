class DataPoint(object):
    def __init__(self, category, values):
        self.category = category
        self.values = values


class DataList(object):
    def __init__(self, data_points):
        self.points = data_points


class DataRow(DataPoint):
    def __init__(self, category, values, parent, order, sort_values):
        DataPoint.__init__(self, category, values)

        self.relationships = {'is_parent': False, 'is_child': False}
        self.order = category
        self.sort_values = values

        if parent:
            is_parent = parent == category
            self.relationships = {'parent': parent,
                                  'is_parent': is_parent,
                                  'is_child': not is_parent}
        if order:
            self.order = order

        if sort_values:
            self.sort_values = sort_values


class DataGroup(object):
    def __init__(self, group, data):
        self.group = group
        self.data = data


class Table(object):
    def __init__(self, header, subtitle, footer, table_type, parent_child, category, category_caption, columns):
        self.header = header
        self.subtitle = subtitle
        self.footer = footer
        self.type = table_type
        self.category = category
        self.columns = columns


class SimpleTable(Table):

    def __init__(self, header, subtitle, footer, parent_child, category, category_caption, columns, data):
        Table.__init__(self,  header, subtitle, footer, 'simple', parent_child, category, category_caption, columns)
        self.data = data


class GroupedTable(Table):

    def __init__(self, header, subtitle, footer, parent_child, category, category_caption, columns,
                 data, groups, group_columns):
        Table.__init__(self, header, subtitle, footer, 'simple', parent_child, category, category_caption, columns)

        self.groups = groups
        self.group_columns = group_columns
        self.data = data

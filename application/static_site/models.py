import json


class DataPoint(object):
    def __init__(self, category, values):
        self.category = category
        self.values = values

    def to_dict(self):
        return {'category': self.category, 'values': self.values}


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

    def to_dict(self):
        dict_value = DataPoint.to_dict(self)
        dict_value['relationships'] = self.relationships
        dict_value['order'] = self.order
        dict_value['sort_values'] = self.sort_values
        return dict_value


class DataGroup(object):
    def __init__(self, group, data):
        self.group = group
        self.data = data

    def to_dict(self):
        return {'group': self.group,
                'data': [row.to_dict() for row in self.data]}


class Table(object):
    def __init__(self, header, subtitle, footer, table_type, parent_child, category, category_caption, columns):
        self.header = header
        self.subtitle = subtitle
        self.footer = footer
        self.type = table_type
        self.category = category
        self.columns = columns
        self.category_caption = category_caption
        self.parent_child = parent_child

    def to_dict(self):
        return {
            'header': self.header, 'subtitle': self.subtitle, 'footer': self.footer,
            'type': self.type,
            'category': self.category, 'category_caption': self.category_caption,
            'columns': self.columns,
            'parent_child': self.parent_child
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class SimpleTable(Table):

    def __init__(self, header, subtitle, footer, parent_child, category, category_caption, columns, data):
        Table.__init__(self,  header, subtitle, footer, 'simple', parent_child, category, category_caption, columns)
        self.data = data

    def to_dict(self):
        dict_value = Table.to_dict(self)
        dict_value['data'] = [row.to_dict() for row in self.data]
        return dict_value


class GroupedTable(Table):

    def __init__(self, header, subtitle, footer, parent_child, category, category_caption, columns,
                 data, groups, group_columns, group_column):
        Table.__init__(self, header, subtitle, footer, 'grouped', parent_child, category, category_caption, columns)

        self.groups = groups
        self.group_column = group_column
        self.group_columns = group_columns
        self.data = data

    def to_dict(self):
        dict_value = Table.to_dict(self)
        dict_value['data'] = [row.to_dict() for row in self.data]
        dict_value['group_column'] = self.group_column
        dict_value['group_columns'] = self.group_columns
        dict_value['groups'] = [group.to_dict() for group in self.groups]
        return dict_value

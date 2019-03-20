class TableObjectDataBuilder:
    """
    Generates table objects that can be used to generate tables on the front end and data download files
    """

    @staticmethod
    def build(table_object):
        if "category_caption" in table_object:
            category_caption = table_object["category_caption"]
        else:
            category_caption = table_object["category"]

        if "group_column" in table_object:
            group_column = table_object["group_column"]
        else:
            group_column = ""

        return {
            "type": table_object["type"],
            "title": table_object["header"],
            "primary_category_column": category_caption,
            "secondary_category_column": group_column,
            "value_columns": table_object["columns"],
            "data": TableObjectDataBuilder.get_data_table(table_object),
        }

    """
    Builds a data table based on an object from the rd-cms table builder
    """

    @staticmethod
    def get_data_table(table_object):

        headers = TableObjectDataBuilder.get_header(table_object)
        data = TableObjectDataBuilder.get_data_rows(table_object)
        return [headers] + data

    @staticmethod
    def get_header(table_object):
        if "category_caption" in table_object and table_object["category_caption"] != "":
            category_caption = table_object["category_caption"]
        else:
            category_caption = table_object["category"]

        if table_object["type"] == "simple":
            return [category_caption] + table_object["columns"]
        if table_object["type"] == "grouped":
            group_caption = table_object["group_column"] if "group_column" in table_object else ""
            return [group_caption, category_caption] + table_object["columns"]

    @staticmethod
    def get_data_rows(table_object):
        if table_object["type"] == "simple":
            return [TableObjectDataBuilder.flat_row(item) for item in table_object["data"] if "category" in item]
        elif table_object["type"] == "grouped":
            group_items = [TableObjectDataBuilder.flat_group(group) for group in table_object["groups"]]
            return [item for group in group_items for item in group]

    @staticmethod
    def flat_row(item):
        return [item["category"]] + item["values"]

    @staticmethod
    def flat_group(group):
        return [TableObjectDataBuilder.flat_row_grouped(item, group["group"]) for item in group["data"]]

    @staticmethod
    def flat_row_grouped(item, group):
        return [group, item["category"]] + item["values"]


class TableObjectTableBuilder:
    @staticmethod
    def build(table_object):
        if table_object["type"] == "simple":
            return TableObjectDataBuilder.build(table_object)
        else:
            table = TableObjectDataBuilder.build(table_object)
            table["data"] = TableObjectTableBuilder.get_data_table(table_object)
            return table

    @staticmethod
    def get_data_table(table_object):
        group_names = [group for group in table_object["group_columns"] if group != ""]
        values = table_object["columns"]
        groups = table_object["groups"]
        groups_data = dict((group["group"], group) for group in groups)
        categories = [item["category"] for item in groups[0]["data"]]
        category = table_object["category_caption"] if "category_caption" in table_object else table_object["category"]

        headers = TableObjectTableBuilder.get_data_table_headers(group_names, values, category)
        rows = TableObjectTableBuilder.get_data_table_rows(categories, group_names, groups_data)

        return headers + rows

    @staticmethod
    def get_data_table_headers(group_names, values, category):
        row1 = [""]
        row2 = [category]

        for group in group_names:
            row1 = row1 + [group] + [""] * (len(values) - 1)
            row2 = row2 + values

        return [row1, row2]

    @staticmethod
    def get_data_table_rows(categories, group_names, groups_data):
        rows = [
            TableObjectTableBuilder.get_row_data_for_category(category, group_names, groups_data)
            for category in categories
        ]
        return rows

    @staticmethod
    def get_row_data_for_category(category, group_names, groups_data):
        data = []
        for group_name in group_names:
            data = data + TableObjectTableBuilder.get_data_for_category_and_group(category, group_name, groups_data)
        return [category] + data

    @staticmethod
    def get_data_for_category_and_group(category, group_name, groups_data):
        group_data = groups_data[group_name]
        for item in group_data["data"]:
            if item["category"] == category:
                return item["values"]

        return None

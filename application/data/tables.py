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

    @staticmethod
    def upgrade_v1_to_v2(table_object, table_settings, dictionary_lookup):
        return {
            "version": "2.0",
            "data": TableObjectDataBuilder.__get_v2_table_data(table_object, table_settings, dictionary_lookup),
            "tableOptions": TableObjectDataBuilder.__get_v2_table_options(table_object, table_settings),
            "tableValues": TableObjectDataBuilder.__get_v2_table_values(table_settings),
        }

    @staticmethod
    def __get_v2_table_values(table_settings):
        return {
            "table_title": table_settings["tableOptions"]["table_title"],
            "table_column_1": table_settings["tableOptions"]["table_column_1"],
            "table_column_2": table_settings["tableOptions"]["table_column_2"],
            "table_column_3": table_settings["tableOptions"]["table_column_3"],
            "table_column_4": table_settings["tableOptions"]["table_column_4"],
            "table_column_5": table_settings["tableOptions"]["table_column_5"],
            # We only want to carry across the column name if the column has been selected for display on the table
            # This is because Table Builder 1 didn't clear out column names/labels if the user changed their mind and
            # decided not to show that column.
            "table_column_1_name": (
                table_settings["tableOptions"]["table_column_1_name"]
                if table_settings["tableOptions"]["table_column_1"] != "none"
                else None
            ),
            "table_column_2_name": (
                table_settings["tableOptions"]["table_column_2_name"]
                if table_settings["tableOptions"]["table_column_2"] != "none"
                else None
            ),
            "table_column_3_name": (
                table_settings["tableOptions"]["table_column_3_name"]
                if table_settings["tableOptions"]["table_column_3"] != "none"
                else None
            ),
            "table_column_4_name": (
                table_settings["tableOptions"]["table_column_4_name"]
                if table_settings["tableOptions"]["table_column_4"] != "none"
                else None
            ),
            "table_column_5_name": (
                table_settings["tableOptions"]["table_column_5_name"]
                if table_settings["tableOptions"]["table_column_5"] != "none"
                else None
            ),
        }

    @staticmethod
    def __get_v2_table_data(table_object, table_settings, dictionary_lookup):

        if table_object["type"] == "simple":
            return TableObjectDataBuilder.__get_v2_simple_data(table_object, table_settings, dictionary_lookup)

        elif TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_category_column"]):
            return TableObjectDataBuilder.__get_v2_ethnicity_is_rows_data(
                table_object, table_settings, dictionary_lookup
            )

        elif TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_group_column"]):
            return TableObjectDataBuilder.__get_v2_ethnicity_is_columns_data(
                table_object, table_settings, dictionary_lookup
            )

        return {}

    @staticmethod
    def __get_v2_simple_data(table_object, table_settings, dictionary_lookup):
        table_data_object = TableObjectDataBuilder.build(table_object)
        table_columns = TableObjectDataBuilder.__get_table_columns(table_settings)
        headers = ["Ethnicity"] + table_columns
        return [headers] + table_data_object["data"][1:]

    @staticmethod
    def __get_v2_ethnicity_is_rows_data(table_object, table_settings, dictionary_lookup):
        data = TableObjectDataBuilder.__get_standardised_data(table_settings, dictionary_lookup)

        required_columns = [
            table_settings["tableOptions"]["table_category_column"],
            table_settings["tableOptions"]["table_group_column"],
        ] + TableObjectDataBuilder.__get_table_columns(table_settings)
        if table_settings["tableOptions"]["table_column_order_column"] not in required_columns:
            required_columns.append(table_settings["tableOptions"]["table_column_order_column"])

        headers = data[0]
        required_indices = [
            headers.index(required_column) for required_column in required_columns if required_column in headers
        ]

        converted = [[row[index] for index in required_indices] for row in data]
        converted[0][0] = "Ethnicity"

        return converted

    @staticmethod
    def __get_v2_ethnicity_is_columns_data(table_object, table_settings, dictionary_lookup):

        data = TableObjectDataBuilder.__get_standardised_data(table_settings, dictionary_lookup)

        required_columns = [
            table_settings["tableOptions"]["table_group_column"],
            table_settings["tableOptions"]["table_category_column"],
        ] + TableObjectDataBuilder.__get_table_columns(table_settings)
        if table_settings["tableOptions"]["table_order_column"] not in required_columns:
            required_columns.append(table_settings["tableOptions"]["table_order_column"])

        headers = data[0]
        required_indices = [
            headers.index(required_column) for required_column in required_columns if required_column in headers
        ]

        converted = [[row[index] for index in required_indices] for row in data]
        converted[0][0] = "Ethnicity"

        return converted

    @staticmethod
    def __get_standardised_data(table_settings, dictionary_lookup):
        return dictionary_lookup.process_data(table_settings["data"])

    @staticmethod
    def __get_table_columns(table_settings):
        return [
            table_column
            for table_column in [
                table_settings["tableOptions"]["table_column_1"],
                table_settings["tableOptions"]["table_column_2"],
                table_settings["tableOptions"]["table_column_3"],
                table_settings["tableOptions"]["table_column_4"],
                table_settings["tableOptions"]["table_column_5"],
            ]
            if (table_column != "none" and table_column != "[None]")
        ]

    @staticmethod
    def __is_ethnicity_column(column_name):
        ETHNICITY_VALUES = ["ethnicity", "ethnic"]
        column_name_lower = column_name.lower().strip()
        for ETHNICITY_VALUE in ETHNICITY_VALUES:
            if ETHNICITY_VALUE in column_name_lower:
                return True
        return False

    @staticmethod
    def __get_v2_table_options(table_object, table_settings):
        if table_object["type"] == "simple":
            return {}

        if TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_category_column"]):
            # Ethnicity defines rows
            data_style = "ethnicity_as_row"
            selection = table_settings["tableOptions"]["table_group_column"]
            order = table_settings["tableOptions"]["table_column_order_column"]

        elif TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_group_column"]):
            # Ethnicity defines column groups
            data_style = "ethnicity_as_column"
            selection = table_settings["tableOptions"]["table_category_column"]
            order = table_settings["tableOptions"]["table_order_column"]

        else:
            # No ethnicity column - return blank
            return {"error": "no ethnicity column"}

        return {"data_style": data_style, "selection": selection, "order": order}

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

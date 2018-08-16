from application.utils import get_bool


class Harmoniser:
    default_sort_value = 800
    default_ethnicity_columns = ["ethnicity", "ethnic group"]
    default_ethnicity_type_columns = ["ethnicity type", "ethnicity_type", "ethnicity-type"]

    """
    Harmoniser adds fields to a dataset

    Harmoniser relies on keeping a csv up to date with appropriate values for data being used on the platform
    """

    def __init__(self, lookup_file, default_values=None, wildcard="*"):
        import csv

        with open(lookup_file, "r") as f:
            reader = csv.reader(f)
            self.lookup = list(reader)
        self.default_values = default_values
        self.wildcard = wildcard
        self.lookup_dict = self.build_dict()

    def build_dict(self):
        dict = {}
        for row in self.lookup:
            ethnicity = row[0].lower().strip()
            ethnicity_type = row[1].lower().strip()
            if ethnicity in dict:
                dict[ethnicity][ethnicity_type] = row
            else:
                item = {ethnicity_type: row}
                dict[ethnicity] = item
        return dict

    def process_data(self, data, ethnicity_name="", ethnicity_type_name=""):
        headers = data.pop(0)
        try:
            if ethnicity_name != "":
                ethnicity_index = self.find_column(headers, [ethnicity_name])
            else:
                ethnicity_index = self.find_column(headers, self.default_ethnicity_columns)
        except ValueError:
            data.insert(0, headers)
            return data

        try:
            if ethnicity_type_name != "":
                ethnicity_type_index = self.find_column(headers, [ethnicity_type_name])
            else:
                ethnicity_type_index = self.find_column(headers, self.default_ethnicity_type_columns)
        except ValueError:
            # default ethnicity type index to use the ethnicity column (essentially ignore ethnicity types)
            ethnicity_type_index = ethnicity_index

        self.append_columns(data, ethnicity_column=ethnicity_index, ethnicity_type_column=ethnicity_type_index)
        headers.extend(self.lookup[0][2:])
        data.insert(0, headers)

        return data

    def find_column(self, headers, column_names):
        lower_headers = [h.lower() for h in headers]
        for column_name in column_names:
            try:
                index = lower_headers.index(column_name.lower())
                return index
            except ValueError:
                pass
        raise ValueError

    def append_columns(self, data, ethnicity_column=0, ethnicity_type_column=1):

        for item in data:
            try:
                ethnicity = item[ethnicity_column].lower().strip()
                ethnicity_type = item[ethnicity_type_column].lower().strip()

                found = False
                if ethnicity in self.lookup_dict:
                    ethnicity_row = self.lookup_dict[ethnicity]
                    if ethnicity_type in ethnicity_row:
                        self.append_dict_values(ethnicity_row[ethnicity_type], item)
                        found = True
                    elif "" in ethnicity_row:
                        self.append_dict_values(ethnicity_row[""], item)
                        found = True

                if found is False:
                    if self.default_values is None:
                        item.extend([""] * (self.lookup[0].__len__() - 2))
                    else:
                        item.extend(
                            self.calculate_column_values(self.wildcard, item[ethnicity_column], self.default_values)
                        )

            except IndexError:
                pass

    def append_dict_values(self, lookup_row, item):
        cells = lookup_row[2:]
        item.extend(cells)

    @staticmethod
    def calculate_column_values(wildcard, substitute, default_values):
        values = []
        for value in default_values:
            try:
                new_value = value.replace(wildcard, substitute)
                values.append(new_value)
            except AttributeError:
                values.append(value)
        return values


class DimensionObjectBuilder:
    """
    Creates an object from table database entries that can be processed using file writers
    """

    def __init__(self):
        self.data_table = [[]]
        self.context = []

    @staticmethod
    def build(dimension):
        dimension_object = {"context": DimensionObjectBuilder.get_context(dimension)}

        if dimension.table:
            dimension_object["table"] = TableObjectDataBuilder.build(dimension.table)

        if dimension.chart:
            dimension_object["chart"] = ChartObjectDataBuilder.build(dimension.chart)

        if dimension.table:
            dimension_object["tabular"] = TableObjectTableBuilder.build(dimension.table)

        return dimension_object

    @staticmethod
    def get_context(dimension):
        return {
            "measure": dimension.page.title,
            "dimension": dimension.title,
            "dimension_uri": "%s/%s" % (dimension.page.uri, dimension.guid) if dimension.page.uri else "",
            "guid": dimension.guid,
            "measure_guid": dimension.page.guid if dimension.page.guid else "",
            "measure_uri": dimension.page.uri if dimension.page.uri else "",
            "time_period": dimension.time_period if dimension.time_period else "",
            "location": dimension.page.format_area_covered(),
            "source_text": dimension.page.source_text if dimension.page.source_text else "",
            "source_url": dimension.page.source_url if dimension.page.source_url else "",
            "department": dimension.page.department_source.name if dimension.page.department_source else "",
            "publication_date": dimension.page.published_date if dimension.page.published_date else "",
        }


class TableObjectDataBuilder:
    """
    Generates table objects that can be used to generate dimension files or api files
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
    def upgrade_v1_to_v2(table_object, table_settings):
        return {
            "version": "2.0",
            "data": TableObjectDataBuilder.__get_v2_table_data(table_object, table_settings),
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
            "table_column_1_name": table_settings["tableOptions"]["table_column_1_name"],
            "table_column_2_name": table_settings["tableOptions"]["table_column_2_name"],
            "table_column_3_name": table_settings["tableOptions"]["table_column_3_name"],
            "table_column_4_name": table_settings["tableOptions"]["table_column_4_name"],
            "table_column_5_name": table_settings["tableOptions"]["table_column_5_name"],
        }

    @staticmethod
    def __get_v2_table_data(table_object, table_settings):

        if table_object["type"] == "simple":
            return TableObjectDataBuilder.__get_v2_simple_data(table_object, table_settings)

        elif TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_category_column"]):
            return TableObjectDataBuilder.__get_v2_ethnicity_is_rows_data(table_object, table_settings)

        elif TableObjectDataBuilder.__is_ethnicity_column(table_settings["tableOptions"]["table_group_column"]):
            return TableObjectDataBuilder.__get_v2_ethnicity_is_columns_data(table_object, table_settings)

        return {}

    @staticmethod
    def __get_v2_simple_data(table_object, table_settings):
        table_data_object = TableObjectDataBuilder.build(table_object)
        table_columns = TableObjectDataBuilder.__get_table_columns(table_settings)
        headers = ["Ethnicity"] + table_columns
        return [headers] + table_data_object["data"][1:]

    @staticmethod
    def __get_v2_ethnicity_is_rows_data(table_object, table_settings):

        data = TableObjectDataBuilder.__get_harmonised_data(table_settings)

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
    def __get_v2_ethnicity_is_columns_data(table_object, table_settings):

        data = TableObjectDataBuilder.__get_harmonised_data(table_settings)

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
    def __get_harmonised_data(table_settings):
        from flask import current_app

        if current_app:
            return current_app.harmoniser.process_data(table_settings["data"])
        else:
            return Harmoniser("application/data/ethnicity_lookup.csv").process_data(table_settings["data"])

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


class ChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):
        builder = None
        if chart_object["type"] == "bar" or chart_object["type"] == "small_bar":
            builder = BarChartObjectDataBuilder
        elif chart_object["type"] == "line":
            builder = LineChartObjectDataBuilder
        elif chart_object["type"] == "component":
            builder = ComponentChartObjectDataBuilder
        elif chart_object["type"] == "panel_bar_chart":
            builder = PanelBarChartObjectDataBuilder
        elif chart_object["type"] == "panel_line_chart":
            builder = PanelLineChartObjectDataBuilder

        if builder:
            return builder.build(chart_object)
        else:
            return None

    @staticmethod
    def upgrade_v1_to_v2(chart_object, chart_settings):

        v2 = ChartObjectDataBuilder.get_v2_chart_type(chart_settings)
        v2["chartFormat"] = chart_settings["chartFormat"]
        v2["version"] = "2.0"

        if v2["type"] == "bar_chart":
            v2["chartOptions"] = {}
            data = [["Ethnicity", "Value"]]
            for item in chart_object["series"][0]["data"]:

                if "text" in item and item["text"] != "number":
                    data += [[item["category"], item["text"]]]
                else:
                    data += [[item["category"], item["y"]]]

            v2["data"] = data

        elif v2["type"] == "line_graph":
            x_axis_column = chart_settings["chartOptions"]["x_axis_column"]
            v2["chartOptions"] = {"x_axis_column": x_axis_column}
            v2["data"] = ChartObjectDataBuilder.get_line_graph_data(chart_object, x_axis_column)

        elif v2["type"] == "grouped_bar_chart":
            if ChartObjectDataBuilder.is_ethnicity_column(chart_settings["chartOptions"]["primary_column"]):
                bar_column = chart_settings["chartOptions"]["secondary_column"]
                v2["chartOptions"] = {"data_style": "ethnicity_as_group", "bar_column": bar_column}
                v2["data"] = ChartObjectDataBuilder.get_grouped_data_ethnicity_is_group(bar_column, chart_object)
            else:
                group_column = chart_settings["chartOptions"]["primary_column"]
                v2["chartOptions"] = {"data_style": "ethnicity_as_bar", "group_column": group_column}
                v2["data"] = ChartObjectDataBuilder.get_grouped_data_ethnicity_is_bar(group_column, chart_object)

        elif v2["type"] == "component_chart":
            if ChartObjectDataBuilder.is_ethnicity_column(chart_settings["chartOptions"]["component_bar_column"]):
                component_column = chart_settings["chartOptions"]["component_component_column"]
                component_order_column = "Order"
                v2["chartOptions"] = {
                    "data_style": "ethnicity_as_bar",
                    "section_column": component_column,
                    "section_order": component_order_column,
                }
                v2["data"] = ChartObjectDataBuilder.get_component_data_ethnicity_is_bar(component_column, chart_object)
            else:
                bar_column = chart_settings["chartOptions"]["component_bar_column"]
                bar_order_column = "Order"
                v2["chartOptions"] = {
                    "data_style": "ethnicity_as_sections",
                    "bar_column": bar_column,
                    "bar_order": bar_order_column,
                }
                v2["data"] = ChartObjectDataBuilder.get_component_data_ethnicity_is_component(bar_column, chart_object)

        elif v2["type"] == "panel_bar_chart":
            if ChartObjectDataBuilder.is_ethnicity_column(chart_settings["chartOptions"]["panel_primary_column"]):
                panel_column = chart_settings["chartOptions"]["panel_grouping_column"]
                panel_order_column = "Order"
                v2["chartOptions"] = {
                    "data_style": "ethnicity_as_panel_bars",
                    "panel_column": panel_column,
                    "panel_order": panel_order_column,
                }
                v2["data"] = ChartObjectDataBuilder.get_panel_bar_data_ethnicity_is_bar(panel_column, chart_object)
            else:
                bar_column = chart_settings["chartOptions"]["panel_primary_column"]
                bar_order_column = "Order"
                v2["chartOptions"] = {
                    "data_style": "ethnicity_as_panels",
                    "bar_column": bar_column,
                    "bar_order": bar_order_column,
                }
                v2["data"] = ChartObjectDataBuilder.get_panel_bar_data_ethnicity_is_panel(bar_column, chart_object)

        elif v2["type"] == "panel_line_chart":
            x_axis_column = chart_settings["chartOptions"]["panel_line_x_axis"]
            v2["chartOptions"] = {"x_axis_column": x_axis_column}
            v2["data"] = ChartObjectDataBuilder.get_panel_line_graph_data(chart_object, x_axis_column)

        return v2

    @staticmethod
    def get_panel_line_graph_data(chart_object, x_axis_column):
        data = [["Ethnicity", x_axis_column, "Value"]]
        for panel in chart_object["panels"]:
            series = panel["series"][0]
            for i in range(0, len(panel["xAxis"]["categories"])):
                data += [[series["name"], panel["xAxis"]["categories"][i], series["data"][i]]]
        return data

    @staticmethod
    def get_panel_bar_data_ethnicity_is_bar(panel_column, chart_object):
        data = [["Ethnicity", panel_column, "Order", "Value"]]
        for p, panel in enumerate(chart_object["panels"]):
            for item in panel["series"][0]["data"]:

                if "text" in item and item["text"] != "number":
                    data += [[item["category"], panel["title"]["text"], p + 10, item["text"]]]
                else:
                    data += [[item["category"], panel["title"]["text"], p + 10, item["y"]]]

        return data

    @staticmethod
    def get_panel_bar_data_ethnicity_is_panel(bar_column, chart_object):
        data = [["Ethnicity", bar_column, "Order", "Value"]]
        for panel in chart_object["panels"]:
            for i, item in enumerate(panel["series"][0]["data"]):
                if "text" in item and item["text"] != "number":
                    data += [[panel["title"]["text"], item["category"], i + 10, item["text"]]]
                else:
                    data += [[panel["title"]["text"], item["category"], i + 10, item["y"]]]
        return data

    @staticmethod
    def get_grouped_data_ethnicity_is_group(bar_column, chart_object):
        data = [["Ethnicity", bar_column, "Value"]]
        for series in chart_object["series"]:
            for item in series["data"]:
                if "text" in item and item["text"] != "number":
                    data += [[item["category"], series["name"], item["text"]]]
                else:
                    data += [[item["category"], series["name"], item["y"]]]
        return data

    @staticmethod
    def get_grouped_data_ethnicity_is_bar(group_column, chart_object):
        data = [["Ethnicity", group_column, "Value"]]
        for series in chart_object["series"]:
            for item in series["data"]:
                if "text" in item and item["text"] != "number":
                    data += [[series["name"], item["category"], item["text"]]]
                else:
                    data += [[series["name"], item["category"], item["y"]]]

        return data

    @staticmethod
    def get_component_data_ethnicity_is_component(bar_column, chart_object):
        data = [["Ethnicity", bar_column, "Order", "Value"]]
        for series in chart_object["series"]:
            for i in range(0, len(series["data"])):
                val = series["data"][i] if series["data"][i] else 0
                data += [[series["name"], chart_object["xAxis"]["categories"][i], 99 - i, val]]
        return data

    @staticmethod
    def get_component_data_ethnicity_is_bar(component_column, chart_object):
        data = [["Ethnicity", component_column, "Order", "Value"]]
        for s, series in enumerate(chart_object["series"]):
            for i in range(0, len(series["data"])):
                val = series["data"][i] if series["data"][i] else 0
                data += [[chart_object["xAxis"]["categories"][i], series["name"], 99 - s, val]]
        return data

    @staticmethod
    def get_line_graph_data(chart_object, x_axis_column):
        data = [["Ethnicity", x_axis_column, "Value"]]
        x_axis_values = chart_object["xAxis"]["categories"]
        for series in chart_object["series"]:
            for i in range(0, len(x_axis_values)):
                data = data + [[series["name"], x_axis_values[i], series["data"][i]]]
        return data

    @staticmethod
    def get_v2_chart_type(chart_settings):
        if chart_settings["type"] != "bar_chart":
            v2 = {"type": chart_settings["type"]}
        elif chart_settings["chartOptions"]["secondary_column"] != "[None]":
            v2 = {"type": "grouped_bar_chart"}
        else:
            v2 = {"type": "bar_chart"}
        return v2

    @staticmethod
    def is_ethnicity_column(title):
        if "ethnicity" in title.lower():
            return True
        else:
            return False


class PanelBarChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):

        return {
            "type": chart_object["type"],
            "title": chart_object["title"]["text"],
            "x-axis": chart_object["xAxis"]["title"].get("text", ""),
            "y-axis": chart_object["yAxis"]["title"].get("text", ""),
            "data": PanelBarChartObjectDataBuilder.panel_bar_chart_data(chart_object),
        }

    @staticmethod
    def panel_bar_chart_data(chart_object):

        panels = chart_object["panels"]

        if len(panels) > 0:
            panel = panels[0]

            if panel["xAxis"]["title"].get("text", "") != "":
                headers = ["", "", panel["xAxis"]["title"].get("text", "")]
            else:
                headers = ["", "", panel["number_format"]["suffix"]]

            rows = []
            for panel in panels:
                panel_name = panel["title"]["text"]
                panel_rows = BarChartObjectDataBuilder.build(panel)["data"][1:]
                for row in panel_rows:
                    rows = rows + [[panel_name] + row]

            return [headers] + rows
        else:
            return []


class PanelLineChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):
        panel_object = {
            "type": chart_object["type"],
            "title": chart_object["title"]["text"],
            "x-axis": "",
            "y-axis": "",
            "data": [],
        }

        panels = chart_object["panels"]
        if len(panels) == 0:
            return panel_object

        panel = panels[0]
        panel_object["x-axis"] = panel["xAxis"]["title"].get("text", "")
        panel_object["y-axis"] = panel["yAxis"]["title"].get("text", "")
        panel_object["data"] = PanelLineChartObjectDataBuilder.panel_line_chart_data(chart_object)

        return panel_object

    @staticmethod
    def panel_line_chart_data(chart_object):

        panels = chart_object["panels"]

        if len(panels) > 0:
            panel = panels[0]

            if panel["yAxis"]["title"].get("text", "") != "":
                headers = ["", panel["xAxis"]["title"].get("text", ""), panel["xAxis"]["title"].get("text", "")]
            else:
                headers = ["", panel["xAxis"]["title"].get("text", ""), panel["number_format"]["suffix"]]

            rows = []
            for panel in panels:
                panel_name = panel["title"]["text"]
                panel_rows = LineChartObjectDataBuilder.build(panel)["data"][1:]
                for row in panel_rows:
                    rows = rows + [row]

            return [headers] + rows
        else:
            return []


class ComponentChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):

        return {
            "type": chart_object["type"],
            "title": chart_object["title"]["text"],
            "x-axis": chart_object["xAxis"]["title"].get("text", ""),
            "y-axis": chart_object["yAxis"]["title"].get("text", ""),
            "data": ComponentChartObjectDataBuilder.component_chart_data(chart_object),
        }

    @staticmethod
    def component_chart_data(chart_object):
        if chart_object["xAxis"]["title"].get("text", "") != "":
            headers = ["", "", chart_object["yAxis"]["title"].get("text", "")]
        else:
            headers = ["", "", chart_object["number_format"]["suffix"]]
        categories = chart_object["xAxis"]["categories"]

        rows = []
        for s in range(0, chart_object["series"].__len__()):
            series = chart_object["series"][s]
            for r in range(0, series["data"].__len__()):
                row = [categories[r], series["name"], series["data"][r]]
                rows = rows + [row]

        return [headers] + rows


class LineChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):

        return {
            "type": chart_object["type"],
            "title": chart_object["title"]["text"],
            "x-axis": chart_object["xAxis"]["title"].get("text", ""),
            "y-axis": chart_object["yAxis"]["title"].get("text", ""),
            "data": LineChartObjectDataBuilder.line_chart_data(chart_object),
        }

    @staticmethod
    def line_chart_data(chart_object):
        if chart_object["xAxis"]["title"].get("text", "") != "":
            headers = ["Ethnicity", "", chart_object["xAxis"]["title"].get("text", "")]
        else:
            headers = ["Ethnicity", "", chart_object["number_format"]["suffix"]]
        categories = chart_object["xAxis"]["categories"]

        rows = []
        for s in range(0, chart_object["series"].__len__()):
            series = chart_object["series"][s]
            for r in range(0, series["data"].__len__()):
                row = [series["name"], categories[r], series["data"][r]]
                rows = rows + [row]

        return [headers] + rows


class BarChartObjectDataBuilder:
    @staticmethod
    def build(chart_object):
        if chart_object["series"].__len__() > 1:
            data = BarChartObjectDataBuilder.multi_series_bar_chart_data(chart_object)
        else:
            data = BarChartObjectDataBuilder.single_series_bar_chart_data(chart_object)

        return {
            "type": chart_object["type"],
            "title": chart_object["title"]["text"],
            "x-axis": chart_object["xAxis"]["title"].get("text", ""),
            "y-axis": chart_object["yAxis"]["title"].get("text", ""),
            "data": data,
        }

    @staticmethod
    def single_series_bar_chart_data(chart_object):
        if chart_object["xAxis"]["title"].get("text", "") != "":
            headers = ["Ethnicity", chart_object["xAxis"]["title"].get("text", "")]
        else:
            headers = ["Ethnicity", chart_object["number_format"]["suffix"]]

        data = chart_object["series"][0]["data"]
        categories = chart_object["xAxis"]["categories"]

        rows = []
        for i in range(0, data.__len__()):
            if type(data[i]) is dict:
                rows = rows + [[categories[i], data[i]["y"]]]
            else:
                rows = rows + [[categories[i], data[i]]]

        return [headers] + rows

    @staticmethod
    def multi_series_bar_chart_data(chart_object):
        if chart_object["xAxis"]["title"].get("text", "") != "":
            headers = ["", "", chart_object["xAxis"]["title"].get("text", "")]
        else:
            headers = ["", "", chart_object["number_format"]["suffix"]]

        categories = chart_object["xAxis"]["categories"]

        rows = []
        for s in range(0, chart_object["series"].__len__()):
            series = chart_object["series"][s]
            for i in range(0, categories.__len__()):
                try:
                    value = series["data"][i]["y"]
                except TypeError:
                    value = series["data"][i]

                rows = rows + [[categories[i], series["name"], value]]

        return [headers] + rows


class AutoDataGenerator:
    """
        The AutoDataGenerator class implements data standardisation functionality.

        The autodata it refers to are extra data attributes that can be derived from the ethnicity value in a row
        These include the default standardised version of that ethnicity, the standardised version in the
        context of a preset, the parent value for that ethnicity and the order it should appear

        'Presets' are definitions of how to display and order a set of values.
        By checking that all values in a list can be covered by a preset and all necessary preset values are covered
        we can say whether the preset is valid for displaying a list of data
        Typically any given list of values will only have one valid preset but it is possible to have several.
        This is particularly true in 5+1 categorisations

        It is called from the /get-valid-presets-for-data endpoint to do backend data calculations

    """

    def __init__(self, standardiser_lookup, preset_lookup):
        """
        Initialise AutoDataGenerator

        For structure of the lookup variables see the constants

        :param standardiser_lookup: a list of rows that contain data to do simple standardisation
        :param preset_lookup: a list of rows that contain data to define presets
        """

        STANDARDISER_ORIGINAL = 0  # input value
        STANDARDISER_STANDARD = 1  # mapped value

        PRESET_CODE = 0  # code for the preset (this corresponds to a categorisation code)
        PRESET_NAME = 1  # name of a preset (e.g. White British and Other)
        PRESET_STANDARD_VALUE = 2  # a value from the list of standards (e.g. Any other ethnicity)
        PRESET_PRESET_VALUE = 3  # a value the standard should map to with this preset (e.g. Other than White British)
        PRESET_PARENT = 4  # the value for the ethnicity parent column
        PRESET_ORDER = 5  # an order value
        PRESET_REQUIRED = 6  # whether the value in PRESET_STANDARD_VALUE is required for the preset to be valid

        self.standards = {row[STANDARDISER_ORIGINAL].lower(): row[STANDARDISER_STANDARD] for row in standardiser_lookup}

        self.presets = AutoDataGenerator.preset_name_and_code_dict(preset_lookup, PRESET_NAME, PRESET_CODE)

        for preset in self.presets:
            preset_rows = [row for row in preset_lookup if row[PRESET_CODE] == preset]
            preset_dict = {
                row[PRESET_STANDARD_VALUE]: {
                    "standard": row[PRESET_STANDARD_VALUE],
                    "preset": row[PRESET_PRESET_VALUE],
                    "parent": row[PRESET_PARENT],
                    "order": row[PRESET_ORDER],
                }
                for row in preset_rows
                if row[1] != ""
            }
            self.presets[preset]["data"] = preset_dict

            self.presets[preset]["required_values"] = list(
                {row[PRESET_PRESET_VALUE] for row in preset_rows if get_bool(row[PRESET_REQUIRED]) is True}
            )

            standard_values = {row[PRESET_PRESET_VALUE] for row in preset_rows}
            self.presets[preset]["size"] = len(standard_values)

    @classmethod
    def preset_name_and_code_dict(cls, preset_lookup, name_column, code_column):
        """
        Create a dictionary that will
        :param preset_lookup: the preset lookup list
        :param name_column: the column index for name
        :param code_column: the column index for the codes
        :return: a dictionary of {code:{code, name}}
        """
        preset_codes = list({row[code_column] for row in preset_lookup})
        presets = {code: {"code": code} for code in preset_codes}
        for code in preset_codes:
            presets[code]["name"] = [row[name_column] for row in preset_lookup if row[code_column] == code][0]
        return presets

    @classmethod
    def from_files(cls, standardiser_file, preset_file):
        """
        Initialise AutoDataGenerator from files

        :param standardiser_file: path to a csv file containing standardisation lookup data
        :param preset_file: path to a csv file containing preset lookup data
        :return: AutoDataGenerator object
        """
        import csv

        standards = [["header"]]
        with open(standardiser_file, "r") as f:
            reader = csv.reader(f)
            standards = list(reader)
        standards = standards[1:]

        presets = [["header"]]
        with open(preset_file, "r") as f:
            reader = csv.reader(f)
            presets = list(reader)
        presets = presets[1:]

        return AutoDataGenerator(standards, presets)

    def build_auto_data(self, values):
        """

        :param values: The ethnicity column from a dataset
        :return: a list of objects for each *valid* preset including the preset as json
        and the data ordered according to the most appropriate ones to use for this data

        build data returns objects of the form
            {
                'preset': { the full json representation of this preset },
                'data' : [ { autodata for each value processed using this preset } ]
            }

        autodata items take the form
            {
                'value': the original value (e.g. Any other ethnicity),
                'standard': the default standard for value (e.g. Other),
                'preset': the standard for value in the context of this preset (e.g. Other inc Chinese)
                'parent': the parent for value in the context of this preset,
                'order': the order for value in the context of this preset
            }

        """
        standardised = self.convert_to_standard_data(values)

        valid_presets = self.get_valid_presets_for_data([value["standard"] for value in standardised])
        auto_data = []

        for preset in valid_presets:
            # generate autodata for each valid preset
            new_autodata = {
                "preset": preset,
                "data": [
                    {
                        "value": value["value"],
                        "standard": preset["data"][value["standard"]]["standard"],
                        "preset": preset["data"][value["standard"]]["preset"],
                        "parent": preset["data"][value["standard"]]["parent"],
                        "order": int(preset["data"][value["standard"]]["order"]),
                    }
                    for value in standardised
                ],
            }

            # 'fit' is the degree to which our autodata matches the original data fed into the build
            new_autodata["fit"] = AutoDataGenerator.preset_fit(new_autodata)

            auto_data.append(new_autodata)

        # we reverse sort by fit
        auto_data.sort(key=lambda p: (-p["fit"], p["preset"]["size"], p["preset"]["name"]))

        # finally add a [custom] preset value (meaning don't use a preset)
        auto_data.append(self.custom_data_autodata(values))

        return auto_data

    def convert_to_standard_data(self, values):
        def val_or_self(value):
            val = value.strip().lower()
            return self.standards[val] if val in self.standards else value

        return [{"value": value, "standard": val_or_self(value)} for value in values]

    def get_valid_presets_for_data(self, values):
        def preset_maps_all_values(preset, values):
            for value in values:
                if value not in preset["data"]:
                    return False
            return True

        def values_cover_preset_required_values(preset, values):
            coverage = {preset["data"][value]["preset"] for value in values}
            for required_value in preset["required_values"]:
                if required_value not in coverage:
                    return False
            return True

        return [
            preset
            for preset in self.presets.values()
            if preset_maps_all_values(preset, values) and values_cover_preset_required_values(preset, values)
        ]

    @staticmethod
    def preset_fit(autodata):
        matches = 0
        for item in autodata["data"]:
            if item["standard"] == item["preset"]:
                matches += 1
        return matches

    def custom_data_autodata(self, values):
        """
        Default data object to use where none of the presets from file are appropriate

        :param values: The ethnicity column from a dataset
        :return: unprocessed data in autodata form
        """
        preset = self.custom_data_preset(values)
        order_dict = {value["value"]: value["order"] for value in preset["data"]}

        custom_autodata = {
            "preset": preset,
            "data": [
                {"value": value, "standard": value, "preset": value, "parent": value, "order": order_dict[value]}
                for value in values
            ],
        }
        return custom_autodata

    def custom_data_preset(self, values):
        data = []
        existing = set()
        for value in values:
            if value not in existing:
                existing.add(value)
                data.append(value)

        return {
            "code": "custom",
            "name": "[Custom]",
            "data": [
                {"value": value, "standard": value, "preset": value, "parent": value, "order": ind}
                for ind, value in enumerate(data)
            ],
        }

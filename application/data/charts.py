from numbers import Number


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

    @staticmethod  # noqa: C901 (complexity)
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
            for index, item in enumerate(series["data"]):
                if isinstance(item, Number):
                    data += [[chart_object["xAxis"]["categories"][index], series["name"], item]]
                elif "text" in item and item["text"] != "number":
                    data += [[item["category"], series["name"], item["text"]]]
                else:
                    data += [[item["category"], series["name"], item["y"]]]
        return data

    @staticmethod
    def get_grouped_data_ethnicity_is_bar(group_column, chart_object):
        data = [["Ethnicity", group_column, "Value"]]
        for series in chart_object["series"]:
            for index, item in enumerate(series["data"]):
                if isinstance(item, Number):
                    data += [[chart_object["xAxis"]["categories"][index], series["name"], item]]
                elif "text" in item and item["text"] != "number":
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

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

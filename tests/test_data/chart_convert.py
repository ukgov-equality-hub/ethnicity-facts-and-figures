bar = {"type": "bar", "title": {"text": "Proportion of prisoners by ethnicity 2016/17"}, "parent_child": False,
       "xAxis": {"title": {"text": "Proportion"},
                 "categories": ["White", "Black", "Mixed", "Asian", "Other", "Not known"]},
       "yAxis": {"title": {"text": "Ethnic Group"}}, "series": [{"name": "Ethnicity", "data": [
        {"y": 71.12375533, "category": "White", "text": "number"},
        {"y": 18.91891892, "category": "Black", "text": "number"},
        {"y": 2.489331437, "category": "Mixed", "text": "number"},
        {"y": 3.556187767, "category": "Asian", "text": "number"},
        {"y": 0.853485064, "category": "Other", "text": "number"},
        {"y": 3.058321479, "category": "Not known", "text": "number"}]}],
       "number_format": {"multiplier": 1, "prefix": "", "suffix": "%", "min": 0, "max": 100}, "parents": [],
       "version": "1.1"}  # nopep8

bar_source = {"data": [["Time", "Ethnicity", "Value", "Numerator"], ["2016/17", "White", "71.12375533", "1000"],
                       ["2016/17", "Black", "18.91891892", "266"], ["2016/17", "Mixed", "2.489331437", "35"],
                       ["2016/17", "Asian", "3.556187767", "50"], ["2016/17", "Other", "0.853485064", "12"],
                       ["2016/17", "Not known", "3.058321479", "43"]],
              "type": "bar_chart",
              "chartOptions": {"primary_column": "Ethnicity", "secondary_column": "[None]", "parent_column": "[None]",
                               "order_column": "[None]", "x_axis_column": "Ethnicity", "line_series_column": "Time",
                               "line_series_order": "[None]", "component_bar_column": "Ethnicity",
                               "component_component_column": "[None]", "component_row_order_column": "[None]",
                               "component_series_order_column": "[None]", "panel_primary_column": "Ethnicity",
                               "panel_grouping_column": "[None]", "panel_line_x_axis": "Time",
                               "panel_line_series": "Ethnicity", "panel_line_order_column": "[None]",
                               "panel_primary_order_column": "[None]", "panel_order_column": "[None]"},
              "chartFormat": {"chart_title": "Proportion of prisoners by ethnicity 2016/17",
                              "x_axis_label": "Proportion", "y_axis_label": "Ethnic Group", "number_format": "percent",
                              "number_format_prefix": "", "number_format_suffix": "", "number_format_min": "",
                              "number_format_max": ""}}  # nopep8

bar_grouped = {"type": "bar",
               "title": {"text": "Percentage of households"},
               "xAxis": {"title": {"text": ""},
                         "categories": ["Higher managerial, administrative and professional occupations",
                                        "Intermediate occupations", "Routine and manual occupations"]},
               "yAxis": {"title": {"text": ""}}, "series": [{"name": "White British", "data": [
        {"y": 82, "category": "Higher managerial, administrative and professional occupations", "text": "number"},
        {"y": 71, "category": "Intermediate occupations", "text": "number"},
        {"y": 52, "category": "Routine and manual occupations", "text": "number"}]}, {"name": "Other", "data": [
        {"y": 55, "category": "Higher managerial, administrative and professional occupations", "text": "number"},
        {"y": 46, "category": "Intermediate occupations", "text": "number"},
        {"y": 28, "category": "Routine and manual occupations", "text": "number"}]}],
               "number_format": {"multiplier": 1, "prefix": "", "suffix": "%", "min": 0, "max": 100},
               "version": "1.1"}  # nopep8

bar_grouped_source = {"data": [["Ethnicity", "NS-SEC group", "Value"],
                               ["White British", "Higher managerial, administrative and professional occupations",
                                "82.00%"], ["White British", "Intermediate occupations", "71.00%"],
                               ["White British", "Routine and manual occupations", "52.00%"],
                               ["Other", "Higher managerial, administrative and professional occupations", "55.00%"],
                               ["Other", "Intermediate occupations", "46.00%"],
                               ["Other", "Routine and manual occupations", "28.00%"]],
                      "type": "bar_chart",
                      "chartOptions": {"primary_column": "NS-SEC group", "secondary_column": "Ethnicity",
                                       "parent_column": "[None]", "order_column": "[None]",
                                       "x_axis_column": "Ethnicity", "line_series_column": "Ethnicity",
                                       "line_series_order": "[None]", "component_bar_column": "Ethnicity",
                                       "component_component_column": "[None]", "component_row_order_column": "[None]",
                                       "component_series_order_column": "[None]", "panel_primary_column": "Ethnicity",
                                       "panel_grouping_column": "[None]", "panel_line_x_axis": "[None]",
                                       "panel_line_series": "Ethnicity", "panel_line_order_column": "[None]",
                                       "panel_primary_order_column": "[None]", "panel_order_column": "[None]"},
                      "chartFormat": {
                          "chart_title": "Percentage of households",  # nopep8
                          "x_axis_label": "", "y_axis_label": "", "number_format": "percent",
                          "number_format_prefix": "", "number_format_suffix": "", "number_format_min": "",
                          "number_format_max": ""}}  # nopep8

bar_grouped_2 = {"type": "bar", "title": {
    "text": "Percentage of pupils meeting the expected standard in mathematics by ethnicity and gender"},
                 "xAxis": {"title": {"text": ""},
                           "categories": ["Asian", "Black", "Chinese", "Mixed", "White", "Other"]},
                 "yAxis": {"title": {"text": ""}},
                 "series": [{"name": "Boys", "data": [
                     {"y": 73, "category": "Asian", "text": "number"},
                     {"y": 69, "category": "Black", "text": "number"},
                     {"y": 88, "category": "Chinese", "text": "number"},
                     {"y": 72, "category": "Mixed", "text": "number"},
                     {"y": 72, "category": "White", "text": "number"},
                     {"y": 70, "category": "Other", "text": "number"}]},
                            {"name": "Girls", "data": [
                                {"y": 76, "category": "Asian", "text": "number"},
                                {"y": 74, "category": "Black", "text": "number"},
                                {"y": 89, "category": "Chinese", "text": "number"},
                                {"y": 75, "category": "Mixed", "text": "number"},
                                {"y": 73, "category": "White", "text": "number"},
                                {"y": 70, "category": "Other", "text": "number"}]}],
                 "number_format": {"multiplier": 1, "prefix": "", "suffix": "%", "min": 0, "max": 100},
                 "version": "1.1"}

bar_grouped_source_2 = {"data": [
    ["Measure", "Time", "Time_type", "Region", "Local Authority", "LA Code", "Ethnicity", "Ethnicity type", "Gender",
     "Gender_type", "Value", "% higher standard"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "White", "DFE", "Boys", "All/Boys/Girls", "72", "19"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Mixed", "DFE", "Boys", "All/Boys/Girls", "72", "21"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Asian", "DFE", "Boys", "All/Boys/Girls", "73", "21"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Black", "DFE", "Boys", "All/Boys/Girls", "69", "18"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Chinese", "DFE", "Boys", "All/Boys/Girls", "88", "43"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Other", "DFE", "Boys", "All/Boys/Girls", "70", "18"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "White", "DFE", "Girls", "All/Boys/Girls", "73", "16"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Mixed", "DFE", "Girls", "All/Boys/Girls", "75", "17"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Asian", "DFE", "Girls", "All/Boys/Girls", "76", "19"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Black", "DFE", "Girls", "All/Boys/Girls", "74", "15"], [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Chinese", "DFE", "Girls", "All/Boys/Girls", "89", "36"],
    [
        "% of pupils",  # nopep8
        "2015 - 2016", "Year", "England", "All", "E92000001", "Other", "DFE", "Girls", "All/Boys/Girls", "70", "15"]],
    "type": "bar_chart",
    "chartOptions": {"primary_column": "Standard Ethnicity", "secondary_column": "Gender",
                     "parent_column": "[None]", "order_column": "Parent-child order",
                     "x_axis_column": "Time", "line_series_column": "Ethnicity",
                     "line_series_order": "[None]", "component_bar_column": "Ethnicity",
                     "component_component_column": "[None]", "component_row_order_column": "[None]",
                     "component_series_order_column": "[None]", "panel_primary_column": "Ethnicity",
                     "panel_grouping_column": "Ethnicity", "panel_line_x_axis": "Time",
                     "panel_line_series": "Ethnicity", "panel_primary_order_column": "[None]",
                     "panel_order_column": "[None]"}, "chartFormat": {
        "chart_title": "Percentage of pupils meeting the expected standard in mathematics by ethnicity and gender",
        "x_axis_label": "", "y_axis_label": "", "number_format": "percent", "number_format_prefix": "",
        "number_format_suffix": "", "number_format_min": "", "number_format_max": ""}}  # nopep8

line = {"type": "line", "title": {
    "text": "Percentage of adults who had visited a heritage site in the past year, by ethnicity over time"},
        "xAxis": {"title": {"text": ""},
                  "categories": ["2005/06", "2006/07", "2007/08", "2008/09", "2009/10", "2010/11", "2011/12", "2012/13",
                                 "2013/14", "2014/15", "2015/16"]}, "yAxis": {"title": {"text": ""}},
        "series": [{"name": "All", "data": [70, 69, 71, 68, 70, 71, 74, 73, 73, 73, 73]},
                   {"name": "White", "data": [72, 72, 73, 71, 71, 73, 76, 75, 74, 75, 75]},
                   {"name": "Other", "data": [51, 48, 54, 50, 50, 54, 61, 57, 60, 56, 57]}],
        "number_format": {"multiplier": 1, "prefix": "", "suffix": "%", "min": 0, "max": 100},
        "version": "1.1"}  # nopep8

line_source = {"data": [["Time", "Ethnicity", "Value"], ["2005/06", "White", "72"], ["2005/06", "Other", "51"],
                        ["2005/06", "All", "70"], ["2006/07", "White", "72"], ["2006/07", "Other", "48"],
                        ["2006/07", "All", "69"], ["2007/08", "White", "73"], ["2007/08", "Other", "54"],
                        ["2007/08", "All", "71"], ["2008/09", "White", "71"], ["2008/09", "Other", "50"],
                        ["2008/09", "All", "68"], ["2009/10", "White", "71"], ["2009/10", "Other", "50"],
                        ["2009/10", "All", "70"], ["2010/11", "White", "73"], ["2010/11", "Other", "54"],
                        ["2010/11", "All", "71"], ["2011/12", "White", "76"], ["2011/12", "Other", "61"],
                        ["2011/12", "All", "74"], ["2012/13", "White", "75"], ["2012/13", "Other", "57"],
                        ["2012/13", "All", "73"], ["2013/14", "White", "74"], ["2013/14", "Other", "60"],
                        ["2013/14", "All", "73"], ["2014/15", "White", "75"], ["2014/15", "Other", "56"],
                        ["2014/15", "All", "73"], ["2015/16", "White", "75"], ["2015/16", "Other", "57"],
                        ["2015/16", "All", "73"]], "type": "line_graph",
               "chartOptions": {"primary_column": "Ethnicity", "secondary_column": "[None]", "parent_column": "[None]",
                                "order_column": "[None]", "x_axis_column": "Time",
                                "line_series_column": "Standard Ethnicity", "line_series_order": "Parent-child order",
                                "component_bar_column": "Ethnicity", "component_component_column": "[None]",
                                "component_row_order_column": "[None]", "component_series_order_column": "[None]",
                                "panel_primary_column": "Ethnicity", "panel_grouping_column": "Ethnicity",
                                "panel_line_x_axis": "Time", "panel_line_series": "Ethnicity",
                                "panel_line_order_column": "[None]", "panel_primary_order_column": "[None]",
                                "panel_order_column": "[None]"}, "chartFormat": {
        "chart_title": "Percentage of adults who had visited a heritage site in the past year, by ethnicity over time",
        "x_axis_label": "", "y_axis_label": "", "number_format": "percent", "number_format_prefix": "",
        "number_format_suffix": "", "number_format_min": "", "number_format_max": ""}}  # nopep8

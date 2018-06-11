from application.utils import get_bool


class Harmoniser:
    default_sort_value = 800
    default_ethnicity_columns = ['ethnicity', 'ethnic group']
    default_ethnicity_type_columns = ['ethnicity type', 'ethnicity_type', 'ethnicity-type']

    """
    Harmoniser adds fields to a dataset

    Harmoniser relies on keeping a csv up to date with appropriate values for data being used on the platform
    """

    def __init__(self, lookup_file, default_values=None, wildcard='*'):
        import csv
        with open(lookup_file, 'r') as f:
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

    def process_data(self, data, ethnicity_name='', ethnicity_type_name=''):
        headers = data.pop(0)
        try:
            if ethnicity_name != '':
                ethnicity_index = self.find_column(headers, [ethnicity_name])
            else:
                ethnicity_index = self.find_column(headers, self.default_ethnicity_columns)
        except ValueError:
            data.insert(0, headers)
            return data

        try:
            if ethnicity_type_name != '':
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
                    elif '' in ethnicity_row:
                        self.append_dict_values(ethnicity_row[''], item)
                        found = True

                if found is False:
                    if self.default_values is None:
                        item.extend([''] * (self.lookup[0].__len__() - 2))
                    else:
                        item.extend(
                            self.calculate_column_values(self.wildcard, item[ethnicity_column], self.default_values))

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
        dimension_object = {'context': DimensionObjectBuilder.get_context(dimension)}

        if dimension.table:
            dimension_object['table'] = TableObjectDataBuilder.build(dimension.table)

        if dimension.chart:
            dimension_object['chart'] = ChartObjectDataBuilder.build(dimension.chart)

        if dimension.table:
            dimension_object['tabular'] = TableObjectTableBuilder.build(dimension.table)

        return dimension_object

    @staticmethod
    def get_context(dimension):
        return {'measure': dimension.page.title,
                'dimension': dimension.title,
                'dimension_uri': '%s/%s' % (dimension.page.uri, dimension.guid) if dimension.page.uri else '',
                'guid': dimension.guid,
                'measure_guid': dimension.page.guid if dimension.page.guid else '',
                'measure_uri': dimension.page.uri if dimension.page.uri else '',
                'time_period': dimension.time_period if dimension.time_period else '',
                'location': dimension.page.format_area_covered(),
                'source_text': dimension.page.source_text if dimension.page.source_text else '',
                'source_url': dimension.page.source_url if dimension.page.source_url else '',
                'department': dimension.page.department_source.name if dimension.page.department_source else '',
                'publication_date': dimension.page.published_date if dimension.page.published_date else ''}


class TableObjectDataBuilder:
    """
    Generates table objects that can be used to generate dimension files or api files
    """

    @staticmethod
    def build(table_object):
        if 'category_caption' in table_object:
            category_caption = table_object['category_caption']
        else:
            category_caption = table_object['category']

        if 'group_column' in table_object:
            group_column = table_object['group_column']
        else:
            group_column = ''

        return {
            'type': table_object['type'],
            'title': table_object['header'],
            'primary_category_column': category_caption,
            'secondary_category_column': group_column,
            'value_columns': table_object['columns'],
            'data': TableObjectDataBuilder.get_data_table(table_object)
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
        if 'category_caption' in table_object and table_object['category_caption'] != '':
            category_caption = table_object['category_caption']
        else:
            category_caption = table_object['category']

        if table_object['type'] == 'simple':
            return [category_caption] + table_object['columns']
        if table_object['type'] == 'grouped':
            group_caption = table_object['group_column'] if 'group_column' in table_object else ''
            return [group_caption, category_caption] + table_object['columns']

    @staticmethod
    def get_data_rows(table_object):
        if table_object['type'] == 'simple':
            return [TableObjectDataBuilder.flat_row(item) for item in table_object['data']]
        elif table_object['type'] == 'grouped':
            group_items = [TableObjectDataBuilder.flat_group(group) for group in table_object['groups']]
            return [item for group in group_items for item in group]

    @staticmethod
    def flat_row(item):
        return [item['category']] + item['values']

    @staticmethod
    def flat_group(group):
        return [TableObjectDataBuilder.flat_row_grouped(item, group['group']) for item in group['data']]

    @staticmethod
    def flat_row_grouped(item, group):
        return [group, item['category']] + item['values']


class TableObjectTableBuilder:

    @staticmethod
    def build(table_object):
        if table_object['type'] == 'simple':
            return TableObjectDataBuilder.build(table_object)
        else:
            table = TableObjectDataBuilder.build(table_object)
            table['data'] = TableObjectTableBuilder.get_data_table(table_object)
            return table

    @staticmethod
    def get_data_table(table_object):
        group_names = [group for group in table_object['group_columns'] if group != '']
        values = table_object['columns']
        groups = table_object['groups']
        groups_data = dict((group['group'], group) for group in groups)
        categories = [item['category'] for item in groups[0]['data']]
        category = table_object['category_caption'] if 'category_caption' in table_object else table_object['category']

        headers = TableObjectTableBuilder.get_data_table_headers(group_names, values, category)
        rows = TableObjectTableBuilder.get_data_table_rows(categories, group_names, groups_data)

        return headers + rows

    @staticmethod
    def get_data_table_headers(group_names, values, category):
        row1 = ['']
        row2 = [category]

        for group in group_names:
            row1 = row1 + [group] + [''] * (len(values) - 1)
            row2 = row2 + values

        return [row1, row2]

    @staticmethod
    def get_data_table_rows(categories, group_names, groups_data):
        rows = [TableObjectTableBuilder.get_row_data_for_category(category, group_names, groups_data)
                for category in categories]
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
        for item in group_data['data']:
            if item['category'] == category:
                return item['values']

        return None


class ChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):
        builder = None
        if chart_object['type'] == 'bar' or chart_object['type'] == 'small_bar':
            builder = BarChartObjectDataBuilder
        elif chart_object['type'] == 'line':
            builder = LineChartObjectDataBuilder
        elif chart_object['type'] == 'component':
            builder = ComponentChartObjectDataBuilder
        elif chart_object['type'] == 'panel_bar_chart':
            builder = PanelBarChartObjectDataBuilder
        elif chart_object['type'] == 'panel_line_chart':
            builder = PanelLineChartObjectDataBuilder

        if builder:
            return builder.build(chart_object)
        else:
            return None

    @staticmethod
    def upgrade_v1_to_v2(chart_object, chart_settings):

        v2 = ChartObjectDataBuilder.get_v2_chart_type(chart_settings)
        v2['chartFormat'] = chart_settings['chartFormat']

        obj = ChartObjectDataBuilder.build(chart_object)

        return v2

    @staticmethod
    def get_v2_chart_type(chart_settings):
        if chart_settings['type'] != 'bar_chart':
            v2 = {'type': chart_settings['type']}
        elif chart_settings['chartOptions']['secondary_column'] != '[None]':
            v2 = {'type': 'grouped_bar_chart'}
        else:
            v2 = {'type': 'bar_chart'}
        return v2


class PanelBarChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):

        return {
            'type': chart_object['type'],
            'title': chart_object['title']['text'],
            'x-axis': chart_object['xAxis']['title']['text'],
            'y-axis': chart_object['yAxis']['title']['text'],
            'data': PanelBarChartObjectDataBuilder.panel_bar_chart_data(chart_object)
        }

    @staticmethod
    def panel_bar_chart_data(chart_object):

        panels = chart_object['panels']

        if len(panels) > 0:
            panel = panels[0]

            if panel['xAxis']['title']['text'] != '':
                headers = ['', '', panel['xAxis']['title']['text']]
            else:
                headers = ['', '', panel['number_format']['suffix']]

            rows = []
            for panel in panels:
                panel_name = panel['title']['text']
                panel_rows = BarChartObjectDataBuilder.build(panel)['data'][1:]
                for row in panel_rows:
                    rows = rows + [[panel_name] + row]

            return [headers] + rows
        else:
            return []


class PanelLineChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):
        panel_object = {
            'type': chart_object['type'],
            'title': chart_object['title']['text'],
            'x-axis': '',
            'y-axis': '',
            'data': []
        }

        panels = chart_object['panels']
        if len(panels) == 0:
            return panel_object

        panel = panels[0]
        panel_object['x-axis'] = panel['xAxis']['title']['text']
        panel_object['y-axis'] = panel['yAxis']['title']['text']
        panel_object['data'] = PanelLineChartObjectDataBuilder.panel_line_chart_data(chart_object)

        return panel_object

    @staticmethod
    def panel_line_chart_data(chart_object):

        panels = chart_object['panels']

        if len(panels) > 0:
            panel = panels[0]

            if panel['yAxis']['title']['text'] != '':
                headers = ['', panel['xAxis']['title']['text'], panel['xAxis']['title']['text']]
            else:
                headers = ['', panel['xAxis']['title']['text'], panel['number_format']['suffix']]

            rows = []
            for panel in panels:
                panel_name = panel['title']['text']
                panel_rows = LineChartObjectDataBuilder.build(panel)['data'][1:]
                for row in panel_rows:
                    rows = rows + [row]

            return [headers] + rows
        else:
            return []


class ComponentChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):

        return {
            'type': chart_object['type'],
            'title': chart_object['title']['text'],
            'x-axis': chart_object['xAxis']['title']['text'],
            'y-axis': chart_object['yAxis']['title']['text'],
            'data': ComponentChartObjectDataBuilder.component_chart_data(chart_object)
        }

    @staticmethod
    def component_chart_data(chart_object):
        if chart_object['xAxis']['title']['text'] != '':
            headers = ['', '', chart_object['yAxis']['title']['text']]
        else:
            headers = ['', '', chart_object['number_format']['suffix']]
        categories = chart_object['xAxis']['categories']

        rows = []
        for s in range(0, chart_object['series'].__len__()):
            series = chart_object['series'][s]
            for r in range(0, series['data'].__len__()):
                row = [categories[r], series['name'], series['data'][r]]
                rows = rows + [row]

        return [headers] + rows


class LineChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):

        return {
            'type': chart_object['type'],
            'title': chart_object['title']['text'],
            'x-axis': chart_object['xAxis']['title']['text'],
            'y-axis': chart_object['yAxis']['title']['text'],
            'data': LineChartObjectDataBuilder.line_chart_data(chart_object)
        }

    @staticmethod
    def line_chart_data(chart_object):
        if chart_object['xAxis']['title']['text'] != '':
            headers = ['Ethnicity', '', chart_object['xAxis']['title']['text']]
        else:
            headers = ['Ethnicity', '', chart_object['number_format']['suffix']]
        categories = chart_object['xAxis']['categories']

        rows = []
        for s in range(0, chart_object['series'].__len__()):
            series = chart_object['series'][s]
            for r in range(0, series['data'].__len__()):
                row = [series['name'], categories[r], series['data'][r]]
                rows = rows + [row]

        return [headers] + rows


class BarChartObjectDataBuilder:

    @staticmethod
    def build(chart_object):
        if chart_object['series'].__len__() > 1:
            data = BarChartObjectDataBuilder.multi_series_bar_chart_data(chart_object)
        else:
            data = BarChartObjectDataBuilder.single_series_bar_chart_data(chart_object)

        return {
            'type': chart_object['type'],
            'title': chart_object['title']['text'],
            'x-axis': chart_object['xAxis']['title']['text'],
            'y-axis': chart_object['yAxis']['title']['text'],
            'data': data
        }

    @staticmethod
    def single_series_bar_chart_data(chart_object):
        if chart_object['xAxis']['title']['text'] != '':
            headers = ['Ethnicity', chart_object['xAxis']['title']['text']]
        else:
            headers = ['Ethnicity', chart_object['number_format']['suffix']]

        data = chart_object['series'][0]['data']
        categories = chart_object['xAxis']['categories']

        rows = []
        for i in range(0, data.__len__()):
            if type(data[i]) is dict:
                rows = rows + [[categories[i], data[i]['y']]]
            else:
                rows = rows + [[categories[i], data[i]]]

        return [headers] + rows

    @staticmethod
    def multi_series_bar_chart_data(chart_object):
        if chart_object['xAxis']['title']['text'] != '':
            headers = ['', '', chart_object['xAxis']['title']['text']]
        else:
            headers = ['', '', chart_object['number_format']['suffix']]

        categories = chart_object['xAxis']['categories']

        rows = []
        for s in range(0, chart_object['series'].__len__()):
            series = chart_object['series'][s]
            for i in range(0, categories.__len__()):
                try:
                    value = series['data'][i]['y']
                except TypeError:
                    value = series['data'][i]

                rows = rows + [[categories[i], series['name'], value]]

        return [headers] + rows


STANDARDISER_ORIGINAL = 0  # input value
STANDARDISER_STANDARD = 1  # mapped value

PRESET_NAME = 0  # name of a preset (i.e. White British and Other)
PRESET_STANDARD_VALUE = 1  # a value from the list of standards (i.e. Any other ethnicity)
PRESET_PRESET_VALUE = 2  # a value the standard should map to with this preset (i.e. Other than White British)
PRESET_PARENT = 3  # the value for the ethnicity parent column
PRESET_ORDER = 4  # an order value
PRESET_REQUIRED = 5


class AutoDataGenerator:
    """
    auto_data = data standardised and formatted using presets

    standardise = convert from a list of data values to a standard list
    preset = a specification for how a set of values should be displayed, grouped and ordered
    """

    def __init__(self, standardiser_lookup, preset_lookup):
        self.standards = {row[STANDARDISER_ORIGINAL].lower(): row[STANDARDISER_STANDARD] for row in standardiser_lookup}

        preset_names = list({row[PRESET_NAME] for row in preset_lookup})

        self.presets = {preset: {'name': preset} for preset in preset_names}
        for preset in preset_names:
            preset_rows = [row for row in preset_lookup if row[PRESET_NAME] == preset]
            preset_dict = {row[PRESET_STANDARD_VALUE]: {
                'standard': row[PRESET_STANDARD_VALUE],
                'preset': row[PRESET_PRESET_VALUE],
                'parent': row[PRESET_PARENT],
                'order': row[PRESET_ORDER]
            } for row in preset_rows if row[1] != ''}
            self.presets[preset]['data'] = preset_dict

            self.presets[preset]['required_values'] = list(
                {row[PRESET_PRESET_VALUE] for row in preset_rows if get_bool(row[PRESET_REQUIRED]) is True})

            standard_values = {row[PRESET_PRESET_VALUE] for row in preset_rows}
            self.presets[preset]['size'] = len(standard_values)

    @classmethod
    def from_files(cls, standardiser_file, preset_file):
        import csv

        standards = [['header']]
        with open(standardiser_file, 'r') as f:
            reader = csv.reader(f)
            standards = list(reader)
        standards = standards[1:]

        presets = [['header']]
        with open(preset_file, 'r') as f:
            reader = csv.reader(f)
            presets = list(reader)
        presets = presets[1:]

        return AutoDataGenerator(standards, presets)

    def convert_to_standard_data(self, values):
        def val_or_self(value):
            val = value.strip().lower()
            return self.standards[val] if val in self.standards else value

        return [{'value': value, 'standard': val_or_self(value)} for value in values]

    def get_valid_presets_for_data(self, values):
        # preset is valid for data if every value is mapped using the preset
        def preset_maps_all_values(preset, values):
            for value in values:
                if value not in preset['data']:
                    return False
            return True

        def values_cover_preset_required_values(preset, values):
            coverage = {preset['data'][value]['preset'] for value in values}
            for required_value in preset['required_values']:
                if required_value not in coverage:
                    return False
            return True

        return [preset for preset in self.presets.values()
                if preset_maps_all_values(preset, values) and values_cover_preset_required_values(preset, values)]

    def build_auto_data(self, values):
        standardised = self.convert_to_standard_data(values)

        valid_presets = self.get_valid_presets_for_data([value['standard'] for value in standardised])
        auto_data = []

        for preset in valid_presets:
            new_preset = {'preset': preset, 'data': [{
                'value': value['value'],
                'standard': preset['data'][value['standard']]['standard'],
                'preset': preset['data'][value['standard']]['preset'],
                'parent': preset['data'][value['standard']]['parent'],
                'order': int(preset['data'][value['standard']]['order'])
            } for value in standardised]}
            auto_data.append(new_preset)

        auto_data.sort(key=lambda p: (p['preset']['size'], p['preset']['name']))
        auto_data.append(self.custom_data_autodata(values))
        return auto_data

    def custom_data_autodata(self, values):
        preset = self.custom_data_preset(values)
        order_dict = {value['value']: value['order'] for value in preset['data']}

        custom_autodata = {'preset': preset, 'data': [{
            'value': value,
            'standard': value,
            'preset': value,
            'parent': value,
            'order': order_dict[value]
        } for value in values]}
        return custom_autodata

    def custom_data_preset(self, values):
        data = []
        existing = set()
        for value in values:
            if value not in existing:
                existing.add(value)
                data.append(value)

        return {'name': '[Custom]', 'data': [
            {
                'value': value,
                'standard': value,
                'preset': value,
                'parent': value,
                'order': ind
            } for ind, value in enumerate(data)
        ]}

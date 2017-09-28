from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np

import csv
import os

from flask import current_app


class DataProcessor:
    """
    Data processor takes a page, iterates through it's source folder, and process the files fit for publication
    """

    def __init__(self):
        self.file_service = current_app.file_service

    """
    main public process
    """

    def process_files(self, page):

        self.process_page_level_files(page)

    """
    setup directories for the page
    """

    def setup_directories(self, page_file_dir):
        data_dir = '%s/data' % page_file_dir

        try:
            os.removedirs(data_dir)
        except FileNotFoundError:
            pass

        os.mkdir(data_dir)

    """
    Process files at the measure level
    (this is as opposed to files at the dimension level)
    """

    def process_page_level_files(self, page):
        page_system = self.file_service.page_system(page)
        # delete existing processed files
        data_files = page_system.list_files(fs_path='data')
        for file_name in data_files:
            page_system.delete(fs_path='data/%s' % file_name)

        # process all source files
        source_files = page_system.list_files('source')
        for path in source_files:
            source_path = 'source/%s' % path
            data_path = 'data/%s' % path
            if self.do_process_as_csv(source_path):
                CsvProcessor(self.file_service).process_page_level_csv(input_path=source_path,
                                                                       output_path=data_path,
                                                                       page=page)
            else:
                with TemporaryDirectory() as tmp_dir:
                    source_tmp = '%s/source.tmp' % tmp_dir
                    page_system.read(fs_path=source_path, local_path=source_tmp)
                    page_system.write(local_path=source_tmp, fs_path=data_path)

    """
    check whether to process as a csv
    """

    def do_process_as_csv(self, path):
        filename, file_extension = os.path.splitext(path)
        return file_extension == '.csv'


class CsvProcessor:
    def __init__(self, file_system_service):
        self.file_service = file_system_service

    def process_page_level_csv(self, input_path, output_path, page):
        MetadataProcessor(self.file_service).process_page_level_file(input_path=input_path,
                                                                     output_path=output_path,
                                                                     page=page)


class MetadataProcessor:
    """
    Processor to add metadata to data documents
    """

    def __init__(self, file_system_service):
        self.file_service = file_system_service

    """
    public process for adding metadata at page level documents
    """

    def process_page_level_file(self, input_path, output_path, page):
        page_system = self.file_service.page_system(page)

        with TemporaryDirectory() as tmp_dir:
            source_path = '%s/source.tmp' % tmp_dir
            page_system.read(fs_path=input_path, local_path=source_path)

            data_path = '%s/data.tmp' % tmp_dir
            with open(data_path, 'w') as output_file:
                writer = csv.writer(output_file)
                self.append_metadata_rows(page, writer)
                self.append_csv_rows(source_path, writer)

            page_system.write(local_path=data_path, fs_path=output_path)

    """
    add the metadata to a csv writer
    """

    def append_metadata_rows(self, page, writer):
        metadata = [['Title:', page.title],
                    ['Time period:', page.time_covered],
                    ['Location:', page.geographic_coverage],
                    ['Source:', page.source_text],
                    ['Department:', page.department_source],
                    ['Last update:', page.last_update_date],
                    ['', ''],
                    ['', '']]
        [writer.writerow(row) for row in metadata]

    """
    stream a second csv from an input stream to a csv writer
    """

    def append_csv_rows(self, input_path, writer):
        with open(input_path, encoding="latin-1") as input_file:
            reader = csv.reader(input_file)
            [writer.writerow(row) for row in reader]


class HarmoniserWithPandas:
    default_sort_value = 800
    default_ethnicity_columns = ['ethnicity', 'ethnic group']
    default_ethnicity_type_columns = ['ethnicity type', 'ethnicity_type', 'ethnicity-type']

    """
    Harmoniser adds fields to a dataset

    Harmoniser relies on keeping a csv up to date with appropriate values for data being used on the platform
    """

    def __init__(self, lookup_file, default_values=None, wildcard='*'):
        self.lookup = pd.read_csv(lookup_file, header=0)
        self.lookup.fillna('')
        self.default_values = default_values
        self.wildcard = wildcard

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
        headers.extend(self.lookup.columns[2:])
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
                filtered = self.lookup[self.lookup['Ethnicity'].str.lower() == item[ethnicity_column].lower().strip()]
                double_filtered = filtered[self.lookup['Ethnicity_type'].str.lower()
                                           == item[ethnicity_type_column].lower().strip()]
                if double_filtered.__len__() > 0:
                    self.append_lookup_values(double_filtered, item)
                elif filtered.__len__() > 0:
                    self.append_lookup_values(filtered, item)
                elif self.default_values is None:
                    item.extend([''] * (self.lookup.columns.__len__() - 2))
                else:
                    item.extend(
                        self.calculate_column_values(self.wildcard, item[ethnicity_column], self.default_values))

            except IndexError:
                pass

    def append_lookup_values(self, lookup_row, item):
        for i in range(2, lookup_row.iloc[0].values.size):
            self.try_append(lookup_row.iloc[0].values[i], item)

    def try_append(self, value, item):
        try:
            if np.isnan(value):
                item.append('')
            else:
                item.append(np.asscalar(value))
        except TypeError:
            item.append(value)

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

    def append_lookup_values(self, lookup_row, item):
        for i in range(2, lookup_row.iloc[0].values.size):
            self.try_append(lookup_row.iloc[0].values[i], item)

    def append_dict_values(self, lookup_row, item):
        cells = lookup_row[2:]
        item.extend(cells)

    def try_append(self, value, item):
        try:
            if np.isnan(value):
                item.append('')
            else:
                item.append(np.asscalar(value))
        except TypeError:
            item.append(value)

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

        return dimension_object

    @staticmethod
    def get_context(dimension):
        return {'measure': dimension.measure.title,
                'dimension': dimension.title,
                'guid': dimension.guid,
                'measure_guid': dimension.measure.guid if dimension.measure.guid else '',
                'measure_uri': dimension.measure.uri if dimension.measure.uri else '',
                'time_period': dimension.time_period if dimension.time_period else '',
                'location': dimension.measure.geographic_coverage if dimension.measure.geographic_coverage else '',
                'source_text': dimension.measure.source_text if dimension.measure.source_text else '',
                'source_url': dimension.measure.source_url if dimension.measure.source_url else '',
                'department': dimension.measure.department_source if dimension.measure.department_source else '',
                'last_update': dimension.measure.last_update_date if dimension.measure.last_update_date else ''}


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
            'data': TableObjectDataBuilder.get_data_table(table_object),
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

        if builder:
            return builder.build(chart_object)
        else:
            return None


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


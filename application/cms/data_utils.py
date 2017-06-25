import pandas as pd
import numpy as np


class Harmoniser:
    default_sort_value = 800
    default_ethnicity_columns = ['ethnicity']
    default_ethnicity_type_columns = ['ethnicity type', 'ethnicity_type', 'ethnicity-type']

    """
    Harmoniser adds four fields to an ethnicity data set.
    Label                   A harmonised version of the ethnicity name
    Parent-child label      A harmonised version of ethnicity name including the parent name
    Parent                  The name of the ethnicity's parent
    Sort                    An Integer

    Using these four fields we can explore more advanced data options

    Harmoniser relies on keeping a csv up to date with appropriate values for data being used on the platform
    """
    def __init__(self, lookup_file):
        self.lookup = pd.read_csv(lookup_file, header=0)
        self.lookup.fillna('')

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
            filtered = self.lookup[item[ethnicity_column] == self.lookup['Ethnicity']]
            double_filtered = filtered[item[ethnicity_type_column] == self.lookup['Ethnicity_type']]
            if double_filtered.__len__() > 0:
                self.append_lookup_values(double_filtered, item)
            elif filtered.__len__() > 0:
                self.append_lookup_values(filtered, item)
            else:
                item.extend([''] * (self.lookup.columns.__len__() - 2))

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

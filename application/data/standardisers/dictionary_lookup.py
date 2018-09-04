class DictionaryLookup:
    default_sort_value = 800
    default_ethnicity_columns = ["ethnicity", "ethnic group"]
    default_ethnicity_type_columns = ["ethnicity type", "ethnicity_type", "ethnicity-type"]

    """
    DictionaryLookup adds standard fields to a dataset

    DictionaryLookup relies on keeping a csv up to date with appropriate values for data being used on the platform
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

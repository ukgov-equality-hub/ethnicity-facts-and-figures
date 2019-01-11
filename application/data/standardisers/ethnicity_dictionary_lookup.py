from application.data.ethnicity_data_set import EthnicityDataset


class EthnicityDictionaryLookup:
    """
    The standardisers add extra fields such as Standardised Ethnicity and Order to a dataset which can be used
    by our front end tools to build tables and charts

    EthnicityDictionaryLookup is our first standardiser used by ChartBuilder1 and TableBuilder1.

    It adds extra fields using a lookup csv with two primary keys Ethnicity and Ethnicity Type.
    This needs to be kept up to date with appropriate values for data being used on the platform

    By default this can be found in application/data/static/standardisers/dictionary_lookup.csv
    """

    def __init__(self, lookup_file, default_values=None, wildcard="*"):

        self.default_values = default_values
        self.wildcard = wildcard
        self.lookup = EthnicityDictionaryLookup.read_list_from_file(lookup_file)
        self.lookup_dict = self.__build_ethnicity_and_type_lookup()

    def process_data(self, data):
        ethnicity_data_set = EthnicityDataset(data)

        self.process_data_set(data_set=ethnicity_data_set)

        return ethnicity_data_set.get_data()

    def process_data_set(self, data_set):
        data_set.append_headers(self.lookup[0][2:])

        for row_index in range(len(data_set)):
            try:
                self.__append_lookup_data_for_row(data_set, row_index)
            except IndexError:
                pass

    def __append_lookup_data_for_row(self, data_set, row_index):
        lookup_data_for_row = self.__find_lookup_values(
            data_set.get_ethnicity(row_index), data_set.get_ethnicity_type(row_index)
        )
        data_set.append_to_row(row_index, lookup_data_for_row)

    def __find_lookup_values(self, ethnicity, ethnicity_type):
        if self.__has_lookup_match(ethnicity, ethnicity_type):
            return self.__find_known_lookup_values(ethnicity, ethnicity_type)

        elif self.__has_lookup_match(ethnicity, ""):
            return self.__find_known_lookup_values(ethnicity, "")

        return self.__build_default_row(ethnicity)

    def __has_lookup_match(self, ethnicity, ethnicity_type):
        clean_ethnicity = ethnicity.lower().strip()
        clean_ethnicity_type = ethnicity_type.lower().strip()
        if clean_ethnicity in self.lookup_dict and clean_ethnicity_type in self.lookup_dict[clean_ethnicity]:
            return True
        else:
            return False

    def __find_known_lookup_values(self, ethnicity, ethnicity_type):
        clean_ethnicity = ethnicity.lower().strip()
        clean_ethnicity_type = ethnicity_type.lower().strip()
        return self.lookup_dict[clean_ethnicity][clean_ethnicity_type][2:]

    def __build_default_row(self, wildcard_substitute):
        if self.default_values is None:
            return self.__build_default_row_with_no_defaults()
        else:
            return self.__build_default_row_with_defaults(wildcard_substitute)

    def __build_default_row_with_defaults(self, wildcard_substitute):
        values = []
        for value in self.default_values:
            try:
                new_value = value.replace(self.wildcard, wildcard_substitute)
                values.append(new_value)
            except AttributeError:
                values.append(value)
        return values

    def __build_default_row_with_no_defaults(self):
        return [""] * (len(self.lookup[0]) - 2)

    @staticmethod
    def read_list_from_file(file_name):
        import csv

        with open(file_name, "r") as f:
            reader = csv.reader(f)
            return list(reader)

    def __build_ethnicity_and_type_lookup(self):
        lookup_dict = {}
        for lookup_row in self.lookup:
            ethnicity = lookup_row[0].lower().strip()
            ethnicity_type = lookup_row[1].lower().strip()
            if ethnicity in lookup_dict:
                lookup_dict[ethnicity][ethnicity_type] = lookup_row
            else:
                item = {ethnicity_type: lookup_row}
                lookup_dict[ethnicity] = item
        return lookup_dict

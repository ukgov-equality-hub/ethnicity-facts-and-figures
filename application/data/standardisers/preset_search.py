from application.utils import get_bool


class PresetSearch:
    """
    The standardisers add extra fields such as Standardised Ethnicity and Order to a dataset which can be used
    by our front end tools to build tables and charts

    PresetSearch is our advanced standardiser used by ChartBuilder2 and TableBuilder2

    PresetSearch uses the observation that government ethnicity data uses certain defined categorisations and that
    these determine how charts and tables should be displayed. See the categorisation dashboard for examples

    PresetSearch uses the list of ethnicities in input data to see which categorisations might apply to input data
    It returns an array of possible ways the data might have standardised columns added according to each categorisation

    By default this can be found in application/data/static/standardisers/dictionary_lookup.csv
    """

    def build_presets_data(self, values):

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

        standardised_values = self.preset_standardiser.standardise(values)

        valid_presets = self.preset_collection.get_valid_presets(standardised_values)

        custom_preset = self.build_custom_preset(values)

        valid_presets.append(custom_preset)

        return valid_presets


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
            new_autodata["fit"] = PresetSearch.preset_fit(new_autodata)

            auto_data.append(new_autodata)

        # we reverse sort by fit
        auto_data.sort(key=lambda p: (-p["fit"], p["preset"]["size"], p["preset"]["name"]))

        # finally add a [custom] preset value (meaning don't use a preset)
        auto_data.append(self.custom_data_autodata(values))

        return auto_data

    def __init__(self, standardiser_lookup, preset_lookup):
        """
        Initialise PresetSearch

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

        self.presets = PresetSearch.preset_name_and_code_dict(preset_lookup, PRESET_NAME, PRESET_CODE)

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

    @staticmethod
    def from_files(standardiser_file, preset_file):

        standards = PresetSearch.__read_data_with_headers_from_file(standardiser_file)
        presets = PresetSearch.__read_data_with_headers_from_file(preset_file)

        return PresetSearch(standards, presets)

    @staticmethod
    def __read_data_with_headers_from_file(file_name):
        import csv

        data = [["header"]]
        with open(file_name, "r") as f:
            reader = csv.reader(f)
            data = list(reader)
        return data[1:]

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

        # PRESET_CODE = 0  # code for the preset (this corresponds to a categorisation code)
        # PRESET_NAME = 1  # name of a preset (e.g. White British and Other)
        # PRESET_STANDARD_VALUE = 2  # a value from the list of standards (e.g. Any other ethnicity)
        # PRESET_PRESET_VALUE = 3  # a value the standard should map to with this preset (e.g. Other than White British)
        # PRESET_PARENT = 4  # the value for the ethnicity parent column
        # PRESET_ORDER = 5  # an order value
        # PRESET_REQUIRED = 6


class PresetSearchBuilder:
    pass


class PresetStandardiser:
    def __init__(self, ethnicity_map=None):
        if ethnicity_map:
            self.ethnicity_map = ethnicity_map
        else:
            self.ethnicity_map = {}

    def __len__(self):
        return len(self.ethnicity_map)

    def add_conversion(self, input_value, standard_value):
        lookup_value = self.simplify_input_value(input_value)
        self.ethnicity_map[lookup_value] = standard_value

    @classmethod
    def simplify_input_value(cls, input_value):
        return input_value.strip().lower()

    @classmethod
    def from_file(cls, file_name):
        pass

    def map(self, value):
        lookup_value = self.simplify_input_value(value)
        if lookup_value in self.ethnicity_map:
            return self.ethnicity_map[lookup_value]
        else:
            return value

    def map_all(self, value_list):
        return [self.map(value) for value in value_list]


class Preset:
    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.standard_to_value_map = {}
        self.values = {}

    def add_value_to_preset_map(self, standard, preset_value):
        self.standard_to_value_map[standard] = preset_value.ethnicity
        self.values[preset_value.ethnicity] = preset_value

    def get_required_ethnicities(self):
        return {value.ethnicity for value in self.values.values() if value.required is True}

    def get_optional_ethnicities(self):
        return {value.ethnicity for value in self.values.values() if value.required is True}

    def is_valid_for_data_set(self, data_set, preset_standardiser):
        ethnicities_in_data = data_set.get_unique_ethnicities()
        mapped_ethnities_in_data = preset_standardiser.map_all(ethnicities_in_data)

        preset_required_ethnicities = self.get_required_ethnicities()
        found_required_ethnicities = 0

        preset_optional_ethnicities = self.get_optional_ethnicities()

        for mapped_ethnicity in mapped_ethnities_in_data:
            if mapped_ethnicity in preset_required_ethnicities:
                found_required_ethnicities += 1
            elif mapped_ethnicity in


    def data_fit_level(self, data_set):
        true_values = 0
        for ethnicity in data_set.get_unique_ethnicities:
            if ethnicity in self.values:
                true_values += 0
        return true_values / len(data_set)


class PresetCollection:
    def __init__(self):
        self.presets = []

    def add_preset(self, preset):
        self.presets.append(preset)

    def get_valid_presets(self, data_set):
        valid_presets = [preset for preset in self.presets if preset.is_valid_for_data_set(data_set)]
        valid_presets.sort(key=lambda preset: -preset.data_fit_level(data_set))
        return valid_presets


class PresetValue:
    def __init__(self, ethnicity, parent, order, required):
        self.ethnicity = ethnicity
        self.parent = parent
        self.order = order
        self.required = required

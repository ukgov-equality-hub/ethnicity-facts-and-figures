from enum import Enum
from application.utils import get_bool


class PresetSearch:
    """
    PresetSearch is our advanced standardiser used by ChartBuilder2 and TableBuilder2

    PresetSearch uses the observation that government ethnicity data uses certain defined categorisations and that
    these determine how charts and tables should be displayed. See the categorisation dashboard for examples

    PresetSearch first converts to ethnicity labels from the Race Disparity Audit standard list
    Then it searches our preset library for possible matches for that particular set of ethnicities
    """

    def build_presets_data(self, raw_ethnicities):
        valid_presets = self.__get_valid_presets(raw_ethnicities)

        preset_data = [preset.get_outputs(raw_ethnicities, self.standardiser) for preset in valid_presets]
        custom_data = Preset.get_custom_data_outputs(raw_ethnicities)

        preset_data.append(custom_data)

        return preset_data

    def __get_valid_presets(self, raw_ethnicities):
        return self.preset_collection.get_valid_presets(raw_ethnicities, self.standardiser)

    def __init__(self, standardiser, preset_collection):
        self.standardiser = standardiser
        self.preset_collection = preset_collection

    @staticmethod
    def from_file(standardiser_file, preset_file):
        standardiser = PresetBuilder.standardiser_from_file(standardiser_file)
        preset_collection = PresetBuilder.preset_collection_from_file(preset_file)
        return PresetSearch(standardiser, preset_collection)


class Standardiser:
    def __init__(self, ethnicity_map=None):
        if ethnicity_map:
            self.ethnicity_map = ethnicity_map
        else:
            self.ethnicity_map = {}

    def __len__(self):
        return len(self.ethnicity_map)

    def add_conversion(self, raw_ethnicity, standard_ethnicity):
        lookup_value = self.simplify_key(raw_ethnicity)
        self.ethnicity_map[lookup_value] = standard_ethnicity

    @classmethod
    def simplify_key(cls, key_value):
        return key_value.strip().lower()

    def standardise(self, raw_ethnicity):
        lookup_value = self.simplify_key(raw_ethnicity)
        if lookup_value in self.ethnicity_map:
            return self.ethnicity_map[lookup_value]
        else:
            return raw_ethnicity

    def standardise_all(self, raw_ethnicity_list):
        return [self.standardise(raw_ethnicity) for raw_ethnicity in raw_ethnicity_list]


class PresetCollection:
    def __init__(self):
        self.presets = []

    def add_preset(self, preset):
        self.presets.append(preset)

    def get_valid_presets(self, raw_ethnicity_list, preset_standardiser):
        valid_presets = [
            preset
            for preset in self.presets
            if preset.is_valid_for_raw_ethnicities(raw_ethnicity_list, preset_standardiser)
        ]
        valid_presets.sort(key=lambda preset: -preset.__data_fit_level(raw_ethnicity_list, preset_standardiser))
        return valid_presets


class Preset:
    def is_valid_for_raw_ethnicities(self, raw_ethnicities, preset_standardiser):
        ethnicities_in_data = raw_ethnicities.get_unique_ethnicities()
        standard_ethnicities_in_data = preset_standardiser.standardise_all(ethnicities_in_data)

        data_fulfills_requirements = self.__has_data_for_all_required_display_ethnicities(standard_ethnicities_in_data)
        preset_can_map_all_data = self.__no_unknown_values(standard_ethnicities_in_data)

        return data_fulfills_requirements and preset_can_map_all_data

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.standard_to_display_ethnicity_map = {}
        self.preset_data_items = {}

    def add_data_item_to_preset(self, standard, preset_data_item):
        self.standard_to_display_ethnicity_map[standard] = preset_data_item.display_ethnicity
        self.preset_data_items[preset_data_item.display_ethnicity] = preset_data_item

    def __has_data_for_all_required_display_ethnicities(self, standard_ethnicity_list):
        required = self.__get_required_display_ethnicities()
        for ethnicity in required:
            if ethnicity not in standard_ethnicity_list:
                return False
        return True

    def __no_unknown_values(self, standard_ethnicity_list):
        for ethnicity in standard_ethnicity_list:
            if ethnicity not in self.preset_data_items:
                return False
        return True

    def __get_required_display_ethnicities(self):
        return {
            preset_item.display_ethnicity
            for preset_item in self.preset_data_items.values()
            if preset_item.required is True
        }

    def __get_optional_display_ethnicities(self):
        return {
            preset_item.display_ethnicity
            for preset_item in self.preset_data_items.values()
            if preset_item.required is True
        }

    def __data_fit_level(self, raw_ethnicities):
        true_values = 0
        for ethnicity in raw_ethnicities:
            if ethnicity in self.preset_data_items:
                true_values += 0
        return true_values

    def get_outputs(self, raw_ethnicities, preset_standardiser):
        return {
            "preset": self.__get_preset_as_dictionary(),
            "data": self.__get_mapped_raw_data(raw_ethnicities, preset_standardiser),
        }

    def __get_preset_as_dictionary(self):
        return {
            "code": self.code,
            "name": self.name,
            "data": [
                {
                    "value": data_item.display_value,
                    "standard": data_item,
                    "preset": data_item,
                    "parent": data_item,
                    "order": ind,
                }
                for ind, data_item in enumerate(self.preset_data_items)
            ],
        }

    def __get_mapped_raw_data(self, raw_ethnicities, preset_standardiser):
        output_data = []
        for raw_ethnicity in raw_ethnicities:
            standard_ethnicity = preset_standardiser.standardise(raw_ethnicity)
            preset_data_item = self.preset_data_items[standard_ethnicity]
            output_data.append(
                {
                    "value": raw_ethnicity,
                    "standard": standard_ethnicity,
                    "preset": preset_data_item.ethnicity,
                    "parent": preset_data_item.parent,
                    "order": preset_data_item.order,
                }
            )
        return output_data

    @staticmethod
    def get_custom_data_outputs(raw_ethnicities):
        custom_preset = Preset.__get_custom_preset(raw_ethnicities)
        custom_standardiser = Preset.__get_custom_standardiser(raw_ethnicities)
        return custom_preset.get_outputs(raw_ethnicities, custom_standardiser)

    @staticmethod
    def __get_custom_preset(raw_ethnicities):
        preset = Preset("custom", "[Custom]")

        unique_raw_values = Preset.__order_preserving_remove_duplicates(raw_ethnicities)
        for ind, value in enumerate(unique_raw_values):
            preset_data_item = PresetDataItem(display_ethnicity=value, parent=value, order=ind, required=True)
            preset.add_data_item_to_preset(value, preset_data_item)
        return preset

    @staticmethod
    def __get_custom_standardiser(raw_ethnicities):
        standardiser = Standardiser()
        for ethnicity in raw_ethnicities:
            standardiser.add_conversion(ethnicity, ethnicity)
        return standardiser

    @staticmethod
    def __order_preserving_remove_duplicates(values):
        unique = []
        existing = set()
        for value in values:
            if value not in existing:
                existing.add(value)
                unique.append(value)
        return unique


class PresetDataItem:
    def __init__(self, display_ethnicity, parent, order, required):
        self.display_ethnicity = display_ethnicity
        self.parent = parent
        self.order = order
        self.required = required


class PresetBuilder:
    @staticmethod
    def standardiser_from_file(file_name):
        standardiser_data = PresetBuilder.__read_data_from_file_no_headers(file_name)
        standardiser = Standardiser()
        for row in standardiser_data:
            standardiser.add_conversion(raw_ethnicity=row[0], standard_ethnicity=row[1])

        return standardiser

    @staticmethod
    def preset_collection_from_file(file_name):
        preset_file_data = PresetBuilder.__read_data_from_file_no_headers(file_name)
        preset_codes = {row[PresetFileDefinition.CODE] for row in preset_file_data}

        preset_collection = PresetCollection()
        for code in preset_codes:
            preset_collection.add_preset(PresetBuilder.__preset_from_data(code, preset_file_data))
        return preset_collection

    @staticmethod
    def __preset_from_data(preset_code, preset_file_data):
        preset_data = [row for row in preset_file_data if row[PresetFileDefinition.CODE] == preset_code]
        preset = Preset(code=preset_data[0][PresetFileDefinition.CODE], name=preset_data[0][PresetFileDefinition.NAME])
        for row in preset_file_data:
            data_item = PresetBuilder.__preset_data_item_from_file_data(row)
            preset.add_data_item_to_preset(row[PresetFileDefinition.STANDARD_VALUE], data_item)

    @staticmethod
    def __preset_data_item_from_file_data(file_row):
        item_is_required = get_bool(file_row[PresetFileDefinition.REQUIRED])
        return PresetDataItem(
            display_ethnicity=file_row[PresetFileDefinition.DISPLAY_VALUE],
            parent=file_row[PresetFileDefinition.PARENT],
            order=file_row[PresetFileDefinition.ORDER],
            required=item_is_required,
        )

    @staticmethod
    def __read_data_from_file_no_headers(file_name):
        import csv

        with open(file_name, "r") as f:
            reader = csv.reader(f)
            data = list(reader)
            if len(data) > 1:
                return data[1:]
        return []


class PresetFileDefinition(Enum):
    CODE = 0
    NAME = 1
    STANDARD_VALUE = 2
    DISPLAY_VALUE = 3
    PARENT = 4
    ORDER = 5
    REQUIRED = 6

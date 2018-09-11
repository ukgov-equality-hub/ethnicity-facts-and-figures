class PresetSearch:
    """
    PresetSearch is our advanced standardiser used by ChartBuilder2 and TableBuilder2

    PresetSearch uses the observation that government ethnicity data uses certain defined categorisations and that
    these determine how charts and tables should be displayed. See the categorisation dashboard for examples

    PresetSearch first converts to ethnicity labels from the Race Disparity Audit standard list
    Then it searches our preset library for possible matches from known categorisations
    """

    def build_presets_data(self, raw_ethnicities):
        valid_presets = self.__get_valid_presets(raw_ethnicities)

        preset_data = [preset.get_outputs(raw_ethnicities, self.standardiser) for preset in valid_presets]
        custom_data = Preset.get_custom_data_outputs(raw_ethnicities)

        all_output_data = preset_data + [custom_data]

        return all_output_data

    def __get_valid_presets(self, raw_ethnicities):
        return self.preset_collection.get_valid_presets(raw_ethnicities, self.standardiser)

    def __init__(self, standardiser, preset_collection):
        self.standardiser = standardiser
        self.preset_collection = preset_collection


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
        valid_presets.sort(key=lambda preset: -preset.get_data_fit_level(raw_ethnicity_list, preset_standardiser))
        return valid_presets


class Preset:
    def is_valid_for_raw_ethnicities(self, raw_ethnicities, preset_standardiser):
        standard_ethnicities_in_data = preset_standardiser.standardise_all(raw_ethnicities)

        return self.is_valid_for_standard_ethnicities(standard_ethnicities_in_data)

    def is_valid_for_standard_ethnicities(self, standard_ethnicities):
        unique_ethnicities = Preset.__remove_duplicates(standard_ethnicities)

        if self.__no_unknown_values(unique_ethnicities):
            return self.__has_data_for_all_required_display_ethnicities(unique_ethnicities)
        else:
            return False

    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.standard_value_to_display_value_map = {}
        self.preset_data_items = {}

    def get_code(self):
        return self.code

    def get_name(self):
        return self.name

    def add_data_item_to_preset(self, standard, preset_data_item):
        self.standard_value_to_display_value_map[standard] = preset_data_item.display_ethnicity
        self.preset_data_items[preset_data_item.display_ethnicity] = preset_data_item

    def __has_data_for_all_required_display_ethnicities(self, standard_ethnicity_list):
        required = self.__get_required_display_ethnicities()
        display_ethnicity_list = [
            self.standard_value_to_display_value_map[standard] for standard in standard_ethnicity_list
        ]
        for ethnicity in required:
            if ethnicity not in display_ethnicity_list:
                return False
        return True

    def __no_unknown_values(self, standard_ethnicity_list):
        for ethnicity in standard_ethnicity_list:
            if ethnicity not in self.standard_value_to_display_value_map:
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

    def get_data_fit_level(self, raw_ethnicities, standardiser):
        true_values = 0
        for raw_ethnicity in raw_ethnicities:
            standard_ethnicity = standardiser.standardise(raw_ethnicity)
            if standard_ethnicity in self.preset_data_items:
                true_values += 1
        return true_values

    def get_outputs(self, raw_ethnicities, preset_standardiser):
        return {
            "preset": self.__get_preset_as_dictionary(),
            "data": self.__get_mapped_raw_data(raw_ethnicities, preset_standardiser),
        }

    def __get_preset_as_dictionary(self):
        standards = list(self.standard_value_to_display_value_map.keys())
        return {
            "code": self.code,
            "name": self.name,
            "map": {
                standard: self.__get_data_item_for_standard_ethnicity(standard).to_dict() for standard in standards
            },
        }

    def __get_mapped_raw_data(self, raw_ethnicities, preset_standardiser):
        output_data = []
        for raw_ethnicity in raw_ethnicities:
            standard_ethnicity = preset_standardiser.standardise(raw_ethnicity)
            preset_data_item = self.__get_data_item_for_standard_ethnicity(standard_ethnicity)
            output_data.append(
                {
                    "raw_value": raw_ethnicity,
                    "standard_value": standard_ethnicity,
                    "display_value": preset_data_item.display_ethnicity,
                    "parent": preset_data_item.parent,
                    "order": preset_data_item.order,
                }
            )
        return output_data

    def __get_data_item_for_standard_ethnicity(self, standard_ethnicity):
        display_ethnicity = self.standard_value_to_display_value_map[standard_ethnicity]
        return self.preset_data_items[display_ethnicity]

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

    @staticmethod
    def __remove_duplicates(values):
        value_set = set(values)
        return list(value_set)


class PresetDataItem:
    def __init__(self, display_ethnicity, parent, order, required):
        self.display_ethnicity = display_ethnicity
        self.parent = parent
        self.order = order
        self.required = required

    def to_dict(self):
        return {
            "display_ethnicity": self.display_ethnicity,
            "parent": self.parent,
            "order": self.order,
            "required": self.required,
        }


class Builder2FrontendConverter:
    # there have been a large number of changes to variable names
    #
    # in order to avoid messing with the front end during the backend refactor this class has been added to maintain
    # the same interface between the two systems

    def __init__(self, current):
        self.current = current

    def convert_to_builder2_format(self):
        return [Builder2FrontendConverter.__convert_preset_output_to_legacy_version(preset) for preset in self.current]

    @staticmethod
    def __convert_preset_output_to_legacy_version(preset_output):
        return {
            "preset": preset_output["preset"],
            "data": [
                Builder2FrontendConverter.__convert_data_output_to_legacy_version(data_output)
                for data_output in preset_output["data"]
            ],
        }

    @staticmethod
    def __convert_data_output_to_legacy_version(data_output):
        value = {
            "value": data_output["raw_value"],
            "standard": data_output["standard_value"],
            "preset": data_output["display_value"],
            "parent": data_output["parent"],
            "order": data_output["order"],
        }
        return value

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union


class EthnicityClassificationFinder:
    """
    EthnicityClassificationFinder is our advanced standardiser used by ChartBuilder2 and TableBuilder2

    EthnicityClassificationFinder uses the observation that government ethnicity data uses certain defined
    classifications and these determine how charts and tables should be displayed. See the dashboards for examples

    EthnicityClassificationFinder first converts raw entry data to standard labels from the Race Disparity Audit
    Then it searches our classification library for possible matches from known classifications
    """

    def __init__(
        self,
        ethnicity_standardiser: EthnicityStandardiser,
        ethnicity_classification_collection: EthnicityClassificationCollection,
    ) -> None:
        self.standardiser = ethnicity_standardiser
        self.classification_collection = ethnicity_classification_collection

    def find_classifications(self, raw_ethnicities: List[str]) -> List[Dict[str, Any]]:
        valid_classifications = self.__get_valid_classifications(raw_ethnicities)

        classification_data = [
            classification.get_outputs(raw_ethnicities, self.standardiser) for classification in valid_classifications
        ]
        custom_data = EthnicityClassification.get_custom_data_outputs(raw_ethnicities)

        all_output_data = classification_data + [custom_data]

        return all_output_data

    @staticmethod
    def find_classifications_for_default_finder(raw_ethnicities):
        custom_data = EthnicityClassification.get_custom_data_outputs(raw_ethnicities)
        return [custom_data]

    def __get_valid_classifications(self, raw_ethnicities):
        return self.classification_collection.get_valid_classifications(raw_ethnicities, self.standardiser)

    def get_classification_collection(self):
        return self.classification_collection


class EthnicityStandardiser:
    def __init__(self, ethnicity_map: Optional[Any] = None) -> None:
        if ethnicity_map:
            self.ethnicity_map = ethnicity_map
        else:
            self.ethnicity_map = {}

    def __len__(self):
        return len(self.ethnicity_map)

    def add_conversion(self, raw_ethnicity: str, standard_ethnicity: str) -> None:
        lookup_value = self.simplify_key(raw_ethnicity)
        self.ethnicity_map[lookup_value] = standard_ethnicity

    @classmethod
    def simplify_key(cls, key_value: str) -> str:
        return key_value.strip().lower()

    def standardise(self, raw_ethnicity: str) -> str:
        lookup_value = self.simplify_key(raw_ethnicity)
        if lookup_value in self.ethnicity_map:
            return self.ethnicity_map[lookup_value]
        else:
            return raw_ethnicity

    def standardise_all(self, raw_ethnicities: List[str]) -> List[str]:
        return [self.standardise(raw_ethnicity) for raw_ethnicity in raw_ethnicities]


class EthnicityClassificationCollection:
    def __init__(self) -> None:
        self.classifications = []

    def add_classification(self, classification: EthnicityClassification) -> None:
        self.classifications.append(classification)

    def add_classifications(self, classifications):
        [self.add_classification(classification) for classification in classifications]

    def get_classifications(self) -> List[EthnicityClassification]:
        return self.classifications

    def get_valid_classifications(
        self, raw_ethnicity_list: List[str], ethnicity_standardiser: EthnicityStandardiser
    ) -> List[EthnicityClassification]:
        valid_classifications = [
            classification
            for classification in self.classifications
            if classification.is_valid_for_raw_ethnicities(raw_ethnicity_list, ethnicity_standardiser)
        ]
        valid_classifications.sort(
            key=lambda classification: -classification.get_data_fit_level(raw_ethnicity_list, ethnicity_standardiser)
        )
        return valid_classifications

    def get_classification_by_id(self, id: str) -> EthnicityClassification:
        for classification in self.classifications:
            if classification.get_id() == id:
                return classification
        return None

    def get_sorted_classifications(self):
        return sorted(
            self.classifications, key=lambda classification: self.__get_classification_sort_key(classification)
        )

    @staticmethod
    def __get_classification_sort_key(classification):
        digits = ""
        for character in classification.get_id():
            if character.isdigit():
                digits += character
            else:
                if len(digits) == 0:
                    return 0, classification.get_long_name()
                else:
                    return int(digits), classification.get_long_name()

        return int(digits), ""


class EthnicityClassificationDataItem:
    """
    An ethnicity classification data item contains the return data for that
    """

    def __init__(self, display_ethnicity: str, parent: str, order: Union[int, str], required: bool) -> None:
        self.display_ethnicity = display_ethnicity
        self.parent = parent
        self.order = order
        self.required = required

    def get_display_ethnicity(self) -> str:
        return self.display_ethnicity

    def get_parent(self) -> str:
        return self.parent

    def is_required(self) -> bool:
        return self.required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "display_ethnicity": self.display_ethnicity,
            "parent": self.parent,
            "order": self.order,
            "required": self.required,
        }


class EthnicityClassification:
    def __init__(self, id: str, name: str, long_name: str = None) -> None:
        self.id = id
        self.name = name
        if long_name:
            self.long_name = long_name
        else:
            self.long_name = name
        self.standard_value_to_display_value_map = {}
        self.classification_data_items = {}

    def get_id(self) -> str:
        return self.id

    def get_name(self):
        return self.name

    def get_long_name(self):
        return self.long_name

    def get_data_items(self) -> dict_values:
        return self.classification_data_items.values()

    def get_display_values(self) -> List[str]:
        values = set([item.get_display_ethnicity() for item in self.get_data_items()])
        return list(values)

    def get_parent_values(self):
        values = set([item.get_parent() for item in self.get_data_items()])
        return list(values)

    def has_parent_child_relationship(self) -> bool:
        for item in self.get_data_items():
            if item.get_parent() != item.get_display_ethnicity():
                return True
        return False

    def is_valid_for_raw_ethnicities(
        self, raw_ethnicities: List[str], ethnicity_standardiser: EthnicityStandardiser
    ) -> bool:
        standard_ethnicities_in_data = ethnicity_standardiser.standardise_all(raw_ethnicities)

        return self.is_valid_for_standard_ethnicities(standard_ethnicities_in_data)

    def is_valid_for_standard_ethnicities(self, standard_ethnicities: List[str]) -> bool:
        unique_ethnicities = EthnicityClassification.__remove_duplicates(standard_ethnicities)

        if self.__no_unknown_values(unique_ethnicities):
            return self.__has_data_for_all_required_display_ethnicities(unique_ethnicities)
        else:
            return False

    def add_data_item_to_classification(
        self, standard: str, classification_data_item: EthnicityClassificationDataItem
    ) -> None:
        self.standard_value_to_display_value_map[standard] = classification_data_item.display_ethnicity
        self.classification_data_items[classification_data_item.display_ethnicity] = classification_data_item

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
            classification_item.display_ethnicity
            for classification_item in self.classification_data_items.values()
            if classification_item.required is True
        }

    def __get_optional_display_ethnicities(self):
        return {
            classification_item.display_ethnicity
            for classification_item in self.classification_data_items.values()
            if classification_item.required is False
        }

    def get_data_fit_level(self, raw_ethnicities: List[str], standardiser: EthnicityStandardiser) -> int:
        true_values = 0
        for raw_ethnicity in raw_ethnicities:
            standard_ethnicity = standardiser.standardise(raw_ethnicity)
            if standard_ethnicity in self.classification_data_items:
                true_values += 1
        return true_values

    def get_outputs(self, raw_ethnicities: List[str], ethnicity_standardiser: EthnicityStandardiser) -> Dict[str, Any]:
        return {
            "classification": self.__get_classification_as_dictionary(),
            "data": self.__get_mapped_raw_data(raw_ethnicities, ethnicity_standardiser),
        }

    def __get_classification_as_dictionary(self):
        standards = list(self.standard_value_to_display_value_map.keys())
        return {
            "id": self.id,
            "name": self.name,
            "map": {standard: self.get_data_item_for_standard_ethnicity(standard).to_dict() for standard in standards},
        }

    def __get_mapped_raw_data(self, raw_ethnicities, ethnicity_standardiser):
        output_data = []
        for raw_ethnicity in raw_ethnicities:
            standard_ethnicity = ethnicity_standardiser.standardise(raw_ethnicity)
            classification_data_item = self.get_data_item_for_standard_ethnicity(standard_ethnicity)
            output_data.append(
                {
                    "raw_value": raw_ethnicity,
                    "standard_value": standard_ethnicity,
                    "display_value": classification_data_item.display_ethnicity,
                    "parent": classification_data_item.parent,
                    "order": classification_data_item.order,
                }
            )
        return output_data

    def get_data_item_for_raw_ethnicity(self, raw_ethnicity, ethnicity_standardiser):
        standard_ethnicity = ethnicity_standardiser.standardise(raw_ethnicity)
        return self.get_data_item_for_standard_ethnicity(standard_ethnicity)

    def get_data_item_for_standard_ethnicity(self, standard_ethnicity: str) -> EthnicityClassificationDataItem:
        display_ethnicity = self.standard_value_to_display_value_map[standard_ethnicity]
        return self.classification_data_items[display_ethnicity]

    @staticmethod
    def get_custom_data_outputs(raw_ethnicities: List[str]) -> Dict[str, Any]:
        custom_classification = EthnicityClassification.__get_custom_classification(raw_ethnicities)
        custom_standardiser = EthnicityClassification.__get_custom_standardiser(raw_ethnicities)
        return custom_classification.get_outputs(raw_ethnicities, custom_standardiser)

    @staticmethod
    def __get_custom_classification(raw_ethnicities: List[str]) -> EthnicityClassification:
        classification = EthnicityClassification("custom", "[Custom]", "[Custom]")

        unique_raw_values = EthnicityClassification.__order_preserving_remove_duplicates(raw_ethnicities)
        for ind, value in enumerate(unique_raw_values):
            classification_data_item = EthnicityClassificationDataItem(
                display_ethnicity=value, parent=value, order=ind, required=True
            )
            classification.add_data_item_to_classification(value, classification_data_item)
        return classification

    @staticmethod
    def __get_custom_standardiser(raw_ethnicities: List[str]) -> EthnicityStandardiser:
        standardiser = EthnicityStandardiser()
        for ethnicity in raw_ethnicities:
            standardiser.add_conversion(ethnicity, ethnicity)
        return standardiser

    @staticmethod
    def __order_preserving_remove_duplicates(values: List[str]) -> List[str]:
        return list(dict.fromkeys(values))

    @staticmethod
    def __remove_duplicates(values: List[str]) -> List[str]:
        value_set = set(values)
        return list(value_set)


class Builder2FrontendConverter:

    # there have been a large number of changes to variable names
    #
    # in order to avoid messing with the front end during the backend refactor this class has been added to maintain
    # the same interface between the two systems

    def __init__(self, current):
        self.current = current

    def convert_to_builder2_format(self):
        return [
            Builder2FrontendConverter.__convert_ethnicity_classification_output_to_builder_2_version(
                classification_output
            )
            for classification_output in self.current
        ]

    @staticmethod
    def __convert_ethnicity_classification_output_to_builder_2_version(classification_output):
        return {
            "preset": classification_output["classification"],
            "data": [
                Builder2FrontendConverter.__convert_data_output_to_legacy_version(data_output)
                for data_output in classification_output["data"]
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


from application.cms.dimension_classification_service import ClassificationLink
from application.cms.exceptions import (
    ClassificationNotFoundException,
    ClassificationFinderClassificationNotFoundException,
)

ALL_STANDARD_VALUE = "All"
UNKNOWN_STANDARD_VALUE = "Unknown"

"""
An ethnicity classification link builder is in charge of taking inputs from the chart and table builder
and matching them against the dashboard classifications

The main public method is build_classification_link which creates a ClassificationLink that can be
used to assign dimension classifications internally
"""


class EthnicityClassificationLinkBuilder:
    def __init__(self, ethnicity_standardiser, ethnicity_classification_collection, classification_service):
        self.ethnicity_standardiser = ethnicity_standardiser
        self.ethnicity_classification_collection = ethnicity_classification_collection
        self.classification_service = classification_service

    def build_classification_link(self, code_from_builder, values_from_builder):
        classification_finder_link = self.__find_link_in_relation_to_classification_finder(
            code_from_builder, values_from_builder
        )
        try:
            database_classification = self.classification_service.get_classification_by_code(
                classification_finder_link.get_code()
            )
            return ClassificationLink(
                database_classification.classification_id,
                classification_finder_link.get_includes_parents(),
                classification_finder_link.get_includes_all(),
                classification_finder_link.get_includes_unknown(),
            )
        except ClassificationNotFoundException:
            raise ClassificationFinderClassificationNotFoundException(
                "Classification finder code %s could not be matched to database" % classification_finder_link.get_code()
            )

    def __find_link_in_relation_to_classification_finder(self, code_from_builder, values_from_builder):
        standard_values = self.ethnicity_standardiser.standardise_all(values_from_builder)
        classification = self.ethnicity_classification_collection.get_classification_by_code(code_from_builder)

        if classification:
            has_parents = self.__has_parents(standard_values, classification)
            has_all = self.__has_all(standard_values)
            has_unknown = self.__has_unknown(standard_values)
            return ClassificationFinderLink(code_from_builder, has_parents, has_all, has_unknown)
        else:
            return None

    def __has_unknown(self, standard_values):
        return UNKNOWN_STANDARD_VALUE in standard_values

    def __has_all(self, standard_values):
        return ALL_STANDARD_VALUE in standard_values

    def __has_parents(self, standard_values, classification):
        if self.__classification_does_use_parent_child(classification):
            return True
        return False

    def __classification_does_use_parent_child(self, classification):
        classification_items = classification.get_data_items()
        for item in classification_items:
            if item.get_display_ethnicity() != item.get_parent():
                return True
        return False

    def __values_include_required_classification_parents(self, classification, standard_values):
        classification_items = classification.get_data_items()
        required_parents = set([item.get_parent() for item in classification_items if item.is_required()])

        displayed_items = set(
            [
                classification.get_data_item_for_standard_ethnicity(value).get_display_ethnicity()
                for value in standard_values
            ]
        )

        return required_parents.issubset(displayed_items)


class ClassificationFinderLink:
    def __init__(self, code, has_parents, has_all, has_unknown):
        self.code = code
        self.has_parents = has_parents
        self.has_all = has_all
        self.has_unknown = has_unknown

    def get_code(self):
        return self.code

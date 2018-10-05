
from application.cms.dimension_classification_service import ClassificationLink
from application.cms.exceptions import (
    ClassificationNotFoundException,
    ClassificationFinderClassificationNotFoundException,
)

from application.cms.classification_service import ClassificationService

ALL_STANDARD_VALUE = "All"
UNKNOWN_STANDARD_VALUE = "Unknown"

"""
An ethnicity classification link builder is in charge of taking inputs from the chart and table builder
and matching them against the dashboard classifications
"""


class EthnicityClassificationLinkBuilder:
    def __init__(self, ethnicity_standardiser, ethnicity_classification_collection):

        # class: EthnicityStandardiser
        self.ethnicity_standardiser = ethnicity_standardiser

        # class: EthnicityClassificationCollection
        self.ethnicity_classification_collection = ethnicity_classification_collection

    #
    def build_internal_classification_link(self, code_from_builder, values_from_builder):
        external_link = self.__find_external_link(code_from_builder, values_from_builder)
        return self.convert_external_link(external_link)

    #
    def convert_external_link(self, external_link):
        try:
            search_code = self.__remove_parent_indicator_from_external_code(external_link.get_code())
            classification = ClassificationService.get_classification_by_id(search_code)
            return ClassificationLink(
                classification.id,
                external_link.get_includes_parents(),
                external_link.get_includes_all(),
                external_link.get_includes_unknown(),
            )
        except ClassificationNotFoundException:
            raise ClassificationFinderClassificationNotFoundException(
                "Classification finder code %s could not be matched to database" % external_link.get_code()
            )

    def __find_external_link(self, external_code, external_values):
        standard_values = self.ethnicity_standardiser.standardise_all(external_values)
        classification = self.ethnicity_classification_collection.get_classification_by_id(external_code)

        if classification:
            has_parents = self.__has_parents(standard_values, classification)
            has_all = self.__has_all(standard_values)
            has_unknown = self.__has_unknown(standard_values)
            return ExternalClassificationFinderLink(external_code, has_parents, has_all, has_unknown)
        else:
            return None

    def __remove_parent_indicator_from_external_code(self, external_code):
        if external_code.endswith("+"):
            search_code = external_code[:-1]
        else:
            search_code = external_code
        return search_code

    def __has_unknown(self, standard_values):
        return UNKNOWN_STANDARD_VALUE in standard_values

    def __has_all(self, standard_values):
        return ALL_STANDARD_VALUE in standard_values

    def __has_parents(self, standard_values, classification):
        if self.__external_classification_does_use_parent_child(classification):
            return self.__values_include_required_external_classification_parents(classification, standard_values)
        return False

    def __external_classification_does_use_parent_child(self, classification):
        classification_items = classification.get_data_items()
        for item in classification_items:
            if item.get_display_ethnicity() != item.get_parent():
                return True
        return False

    def __values_include_required_external_classification_parents(self, classification, standard_values):
        classification_items = classification.get_data_items()
        required_parents = set([item.get_parent() for item in classification_items if item.is_required()])

        displayed_items = set(
            [
                classification.get_data_item_for_standard_ethnicity(value).get_display_ethnicity()
                for value in standard_values
            ]
        )

        return required_parents.issubset(displayed_items)


class ExternalClassificationFinderLink:
    def __init__(self, code, has_parents, has_all, has_unknown):
        self.code = code
        self.has_parents = has_parents
        self.has_all = has_all
        self.has_unknown = has_unknown

    def get_code(self):
        return self.code

    def get_includes_parents(self):
        return self.has_parents

    def get_includes_all(self):
        return self.has_all

    def get_includes_unknown(self):
        return self.has_unknown

from application.cms.classification_service import ClassificationWithIncludesParentsAllUnknown, ClassificationService
from application.cms.exceptions import (
    ClassificationNotFoundException,
    ClassificationFinderClassificationNotFoundException,
)
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationCollection
from application.data.standardisers.ethnicity_classification_finder import EthnicityStandardiser
from typing import List

ALL_STANDARD_VALUE = "All"
UNKNOWN_STANDARD_VALUE = "Unknown"

"""
An ethnicity classification matcher is in charge of taking inputs from the chart and table builder
and matching them against the dashboard classifications
"""


class EthnicityClassificationMatcher:
    def __init__(
        self,
        ethnicity_standardiser: EthnicityStandardiser,
        ethnicity_classification_collection: EthnicityClassificationCollection,
    ) -> None:

        # class: EthnicityStandardiser
        self.ethnicity_standardiser = ethnicity_standardiser

        # class: EthnicityClassificationCollection
        self.ethnicity_classification_collection = ethnicity_classification_collection

    def get_classification_from_builder_values(
        self, id_from_builder: str, values_from_builder: List[str]
    ) -> ClassificationWithIncludesParentsAllUnknown:
        builder_classification = self.__find_builder_classification(id_from_builder, values_from_builder)
        return self.convert_builder_classification_to_classification(builder_classification)

    def convert_builder_classification_to_classification(
        self, builder_classification: BuilderClassification
    ) -> ClassificationWithIncludesParentsAllUnknown:
        try:
            # IDs from Chart and Table builders can have a "+" on the end, indicating that the data includes parents.
            # We don't have these "+" codes in our database and instead use the "includes_parents" flag, so strip any
            # "+" from the end before looking up in the DB.
            search_id = builder_classification.get_id().rstrip("+")
            classification = ClassificationService.get_classification_by_id(search_id)
            return ClassificationWithIncludesParentsAllUnknown(
                classification.id,
                builder_classification.get_includes_parents(),
                builder_classification.get_includes_all(),
                builder_classification.get_includes_unknown(),
            )
        except ClassificationNotFoundException:
            raise ClassificationFinderClassificationNotFoundException(
                "Classification finder id %s could not be matched to database" % builder_classification.get_id()
            )

    def __find_builder_classification(self, builder_id, builder_values):
        standard_values = self.ethnicity_standardiser.standardise_all(builder_values)
        classification = self.ethnicity_classification_collection.get_classification_by_id(builder_id)

        if classification:
            has_parents = self.__has_parents(standard_values, classification)
            has_all = self.__has_all(standard_values)
            has_unknown = self.__has_unknown(standard_values)
            return BuilderClassification(builder_id, has_parents, has_all, has_unknown)
        else:
            return None

    def __has_unknown(self, standard_values):
        return UNKNOWN_STANDARD_VALUE in standard_values

    def __has_all(self, standard_values):
        return ALL_STANDARD_VALUE in standard_values

    def __has_parents(self, standard_values, classification):
        if self.__builder_classification_does_use_parent_child(classification):
            return self.__builder_classification_values_include_required_parents(classification, standard_values)
        return False

    def __builder_classification_does_use_parent_child(self, classification):
        classification_items = classification.get_data_items()
        for item in classification_items:
            if item.get_display_ethnicity() != item.get_parent():
                return True
        return False

    def __builder_classification_values_include_required_parents(self, classification, standard_values):
        classification_items = classification.get_data_items()
        required_parents = set([item.get_parent() for item in classification_items if item.is_required()])

        displayed_items = set(
            [
                classification.get_data_item_for_standard_ethnicity(value).get_display_ethnicity()
                for value in standard_values
            ]
        )

        return required_parents.issubset(displayed_items)


# This differs from ClassificationWithIncludesParentsAllUnknown only in the naming of the variables.
# Here we have has_... but there we have includes_...
# This is because chart and table builders use has_... and database model uses includes_...
# TODO: Fix this so the front end and back end speak the same language
class BuilderClassification:
    def __init__(self, id: str, has_parents: bool, has_all: bool, has_unknown: bool) -> None:
        self.id = id
        self.has_parents = has_parents
        self.has_all = has_all
        self.has_unknown = has_unknown

    def get_id(self) -> str:
        return self.id

    def get_includes_parents(self) -> bool:
        return self.has_parents

    def get_includes_all(self) -> bool:
        return self.has_all

    def get_includes_unknown(self) -> bool:
        return self.has_unknown

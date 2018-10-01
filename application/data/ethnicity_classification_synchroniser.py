

from application.cms.exceptions import ClassificationNotFoundException

"""
A synchroniser uses the standardiser settings csv as our single source of truth

Matching is done on classification code
"""


class EthnicityClassificationSynchroniser:
    def __init__(self, classification_service):
        self.classification_service = classification_service

    def synchronise_classifications(self, ethnicity_classification_collection):
        classifications = ethnicity_classification_collection.get_classifications()
        classifications.sort(key=lambda classification: self.__split_classification_code(classification.code))

        for index, classification in enumerate(ethnicity_classification_collection.get_classifications()):
            if classification.code.endswith("+") is not True:
                self.__synchronise_classification(classification, position=index)

        self.__update_not_applicable()

    def __split_classification_code(self, classification_code):
        digits = [character for character in classification_code if character.isdigit()]
        if len(digits) > 0:
            number_part = int("".join(digits))
            return number_part, classification_code[len(digits) :]
        else:
            return 1000, classification_code

    def __synchronise_classification(self, classification, position=999):
        try:
            self.__update_database_classification(classification, position=position)
        except ClassificationNotFoundException:
            self.__create_database_classification(classification, position=position)

    def __update_database_classification(self, classification, position):
        database_classification = self.classification_service.get_classification_by_code(
            "Ethnicity", classification.code
        )
        database_classification.title = classification.name
        database_classification.long_title = classification.long_name
        database_classification.subfamily = ""
        database_classification.position = position
        self.classification_service.update_classification(database_classification)

    def __create_database_classification(self, classification, position):
        values = classification.get_display_values()
        if classification.has_parent_child_relationship():
            parents = classification.get_parent_values()
        else:
            parents = []

        self.classification_service.create_classification_with_values(
            classification.code,
            "Ethnicity",
            "",
            classification.name,
            long_title=classification.long_name,
            position=position,
            values=values,
            values_as_parent=parents,
        )

    def __update_not_applicable(
        self, na_code="NA", na_title="Not applicable", na_long_title="Not applicable", na_position=9999
    ):
        try:
            na_classification = self.classification_service.get_classification_by_code("Ethnicity", na_code)
            na_classification.title = na_title
            na_classification.long_title = na_long_title
            na_classification.subfamily = ""
            na_classification.position = na_position
            self.classification_service.update_classification(na_classification)
        except ClassificationNotFoundException:
            pass

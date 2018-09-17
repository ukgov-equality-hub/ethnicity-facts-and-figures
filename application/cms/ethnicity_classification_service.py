from application.cms.classification_service import ClassificationService


class EthnicityClassificationService:
    classification_service = None

    def __init__(self):
        self.classification_service = ClassificationService()

    def initialise_classification_service(self, classification_service):
        self.classification_service = classification_service

    def set_dimension_classification(self, dimension, classification_link):
        classification = self.classification_service.get_classification_by_code(classification_link.code)

        self.classification_service.unlink_dimension_from_family(dimension, "Ethnicity")
        self.classification_service.link_classification_to_dimension(
            dimension,
            classification,
            classification_link.includes_parents,
            classification_link.includes_all,
            classification_link.includes_unknown,
        )

    def get_dimension_classification(self, dimension):
        return self.classification_service.get_classification_link_for_dimension_by_family(dimension, "Ethnicity")

    def set_chart_classification(self, dimension, chart_classification_link):
        pass

    def get_chart_classification(self, dimension):
        pass

    def set_table_classification(self, dimension, table_classification_link):
        pass

    def get_table_classification(self, dimension):
        pass

    def _dimension_table_is_more_detailed(self, dimension):
        pass

    def get_classification(self, classification_code):
        return self.classification_service.get_classification_by_code(classification_code)

    def get_all_classifications(self):
        return self.classification_service.get_classifications_by_family("Ethnicity")


ethnicity_classification_service = EthnicityClassificationService()


class EthnicityClassificationLink:
    def __init__(self, code, includes_parents=False, includes_all=False, includes_unknown=False):
        self.code = code
        self.includes_parents = includes_parents
        self.includes_all = includes_all
        self.includes_unknown = includes_unknown

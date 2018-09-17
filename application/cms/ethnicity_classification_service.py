from application.cms.classification_service import ClassificationService


class EthnicityClassificationService:
    classification_service = None

    def __init__(self):
        self.classification_service = ClassificationService()

    def init_classification_service(self, classification_service):
        self.classification_service = classification_service

    def set_dimension_classification(self, dimension, classification_link):
        self.classification_service.unlink_dimension_from_family(dimension, "Ethnicity")
        self.classification_service.link_classification_to_dimension(dimension, classification_link)

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

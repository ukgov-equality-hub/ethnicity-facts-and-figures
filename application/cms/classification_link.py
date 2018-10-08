from application.cms.classification_service import classification_service


class ClassificationLink:
    def __init__(self, classification_id, includes_parents=False, includes_all=False, includes_unknown=False):
        self.classification_id = classification_id
        self.includes_parents = includes_parents
        self.includes_all = includes_all
        self.includes_unknown = includes_unknown

    def get_classification(self):
        return classification_service.get_classification_by_id(self.classification_id)

    def is_more_complex_than(self, link):
        return self.__get_classification_complexity(self) > self.__get_classification_complexity(link)

    @staticmethod
    def __get_classification_complexity(link):
        classification = link.get_classification()
        complexity = len(classification.values)
        return complexity

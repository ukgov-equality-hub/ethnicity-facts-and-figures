import logging

from application import db
from application.cms.classification_service import classification_service
from application.cms.exceptions import DimensionClassificationNotFoundException
from application.cms.models import DimensionClassification
from application.cms.service import Service

logger = logging.Logger(__name__)

"""
Classifications are assigned to dimensions through the chart and table builder
"""


class DimensionClassificationService(Service):
    def __init__(self):
        super().__init__()

    @staticmethod
    def set_chart_classification_on_dimension(dimension, chart_link):
        classification_to_link_to = chart_link.get_classification()
        family = classification_to_link_to.family
        try:
            DimensionClassificationService.__update_dimension_chart_link(chart_link, dimension, family)
        except DimensionClassificationNotFoundException:
            DimensionClassificationService.__create_dimension_chart_link(chart_link, dimension)

    @staticmethod
    def __create_dimension_chart_link(chart_link, dimension):
        link = DimensionClassificationLink(chart_link, None)
        dimension_classification_service.__add_dimension_classification_link(dimension, link)

    @staticmethod
    def __update_dimension_chart_link(chart_link, dimension, family):
        current = dimension_classification_service.__get_dimension_classification_database_object(dimension, family)
        link = DimensionClassificationLink.from_database_object(current)
        link.set_chart_link(chart_link)
        dimension_classification_service.__update_dimension_classification_link(dimension, link)

    def remove_chart_classification_on_dimension(self, dimension, family):
        link = self.get_dimension_classification_link(dimension, family)
        link.set_chart_link(None)
        self.__save_family_link(dimension, family, link)

    def __save_family_link(self, dimension, family, link):
        if link.table_link is None and link.chart_link is None:
            self.remove_dimension_classification_link(dimension, family)
        else:
            self.__update_dimension_classification_link(dimension, link)

    @staticmethod
    def set_table_classification_on_dimension(dimension, table_link):
        classification_to_link_to = table_link.get_classification()
        family = classification_to_link_to.family
        try:
            DimensionClassificationService.__update_dimension_table_link(table_link, dimension, family)
        except DimensionClassificationNotFoundException:
            DimensionClassificationService.__create_dimension_table_link(table_link, dimension)

    @staticmethod
    def __create_dimension_table_link(table_link, dimension):
        link = DimensionClassificationLink(chart_link=None, table_link=table_link)
        dimension_classification_service.__add_dimension_classification_link(dimension, link)

    @staticmethod
    def __update_dimension_table_link(table_link, dimension, family):
        link = DimensionClassificationService.get_dimension_classification_link(dimension, family)
        link.set_table_link(table_link)
        dimension_classification_service.__update_dimension_classification_link(dimension, link)

    def remove_table_classification_on_dimension(self, dimension, family):
        link = self.get_dimension_classification_link(dimension, family)
        link.set_table_link(None)
        self.__save_family_link(dimension, family, link)

    @staticmethod
    def __get_dimension_classification_database_object(dimension, family):
        for link in dimension.classification_links:
            if link.classification.family == family:
                return link
        raise DimensionClassificationNotFoundException()

    @staticmethod
    def get_dimension_classification_link(dimension, family):
        database_object = dimension_classification_service.__get_dimension_classification_database_object(
            dimension, family
        )
        return DimensionClassificationLink.from_database_object(database_object)

    def __add_dimension_classification_link(self, dimension, link):
        database_link = link.to_database_object(dimension)
        db.session.add(database_link)
        db.session.commit()

    def __update_dimension_classification_link(self, dimension, link):
        family = link.main_link.get_classification().family
        self.remove_dimension_classification_link(dimension, family)
        self.__add_dimension_classification_link(dimension, link)

    def remove_dimension_classification_link(self, dimension, family):
        try:
            link = dimension_classification_service.__get_dimension_classification_database_object(dimension, family)
            db.session.delete(link)
            db.session.commit()
        except DimensionClassificationNotFoundException:
            self.logger.info("Error removing link for '{}' from dimension '{}".format(family, dimension.guid))


class DimensionClassificationLink:
    def __init__(self, chart_link, table_link):
        self.chart_link = chart_link
        self.table_link = table_link
        self.main_link = self.__calculate_main_link()

    @staticmethod
    def from_database_object(dimension_classification):
        chart_link = (
            ClassificationLink(
                classification_id=dimension_classification.chart_classification_id,
                includes_all=dimension_classification.chart_includes_all,
                includes_parents=dimension_classification.chart_includes_parents,
                includes_unknown=dimension_classification.chart_includes_unknown,
            )
            if dimension_classification.chart_classification_id is not None
            else None
        )

        table_link = (
            ClassificationLink(
                classification_id=dimension_classification.table_classification_id,
                includes_all=dimension_classification.table_includes_all,
                includes_parents=dimension_classification.table_includes_parents,
                includes_unknown=dimension_classification.table_includes_unknown,
            )
            if dimension_classification.table_classification_id is not None
            else None
        )

        return DimensionClassificationLink(chart_link, table_link)

    def to_database_object(self, dimension):
        return DimensionClassification(
            dimension_guid=dimension.guid,
            classification_id=self.main_link.classification_id if self.main_link else None,
            includes_parents=self.main_link.includes_parents if self.main_link else None,
            includes_all=self.main_link.includes_all if self.main_link else None,
            includes_unknown=self.main_link.includes_unknown if self.main_link else None,
            chart_classification_id=self.chart_link.classification_id if self.chart_link else None,
            chart_includes_parents=self.chart_link.includes_parents if self.chart_link else None,
            chart_includes_all=self.chart_link.includes_all if self.chart_link else None,
            chart_includes_unknown=self.chart_link.includes_unknown if self.chart_link else None,
            table_classification_id=self.table_link.classification_id if self.table_link else None,
            table_includes_parents=self.table_link.includes_parents if self.table_link else None,
            table_includes_all=self.table_link.includes_all if self.table_link else None,
            table_includes_unknown=self.table_link.includes_unknown if self.table_link else None,
        )

    def __calculate_main_link(self):
        if self.table_link is None:
            return self.chart_link
        elif self.chart_link is None:
            return self.table_link
        elif self.chart_link.is_more_complex_than(self.table_link):
            return self.chart_link
        else:
            return self.table_link

    def set_chart_link(self, chart_link):
        self.chart_link = chart_link

    def set_table_link(self, table_link):
        self.table_link = table_link


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


dimension_classification_service = DimensionClassificationService()

import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.classification_service import classification_service
from application.cms.exceptions import ClassificationNotFoundException, DimensionClassificationNotFoundException

from application.cms.models import Page, Dimension, Classification, ClassificationValue, DimensionClassification
from application.cms.service import Service

from application.utils import setup_module_logging, get_bool
from application import db

logger = logging.Logger(__name__)

"""
Classifications are assigned to dimensions using the chart and table builder
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
        dimension_classification_service.add_dimension_classification_link(dimension, link)

    @staticmethod
    def __update_dimension_chart_link(chart_link, dimension, family):
        current = dimension_classification_service.get_dimension_classification_link(dimension, family)
        link = DimensionClassificationLink.from_database_object(current)
        link.set_chart_link(chart_link)
        dimension_classification_service.update_dimension_classification_link(dimension, link)

    @staticmethod
    def set_table_classification_on_dimension(dimension, classification_link):
        pass

    @staticmethod
    def set_main_classification_manually(dimension, classification_link):
        pass

    @staticmethod
    def get_dimension_classification_link(dimension, family):
        for link in dimension.classification_links:
            if link.classification.family == family:
                return link
        raise DimensionClassificationNotFoundException()

    def add_dimension_classification_link(self, dimension, link):
        pass

    def update_dimension_classification_link(self, dimension, link):
        pass

    def remove_dimension_classification_link(self, dimension, family):
        try:
            link = dimension_classification_service.get_dimension_classification_link(dimension, family)
            db.session.delete(link)
        except DimensionClassificationNotFoundException:
            self.logger.info("Error removing link for '{}' from dimension '{}".format(family, dimension.guid))


class DimensionClassificationLink:
    def __init__(self, chart_link, table_link):
        self.chart_link = chart_link
        self.table_link = table_link
        self.dimension_link = self.get_dimension_link()

    @staticmethod
    def from_database_object(dimension_categorisation):
        return DimensionClassificationLink(None, None)


    def to_database_link(self):
        return DimensionClassification(

        )


    def get_dimension_link(self):
        return None

    def get_dimension_categorisation(self, dimension):
        pass

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


dimension_classification_service = DimensionClassificationService()

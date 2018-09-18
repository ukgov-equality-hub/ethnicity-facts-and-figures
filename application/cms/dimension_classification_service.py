import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import ClassificationNotFoundException

from application.cms.models import Page, Dimension, Classification, ClassificationValue, DimensionClassification

from application.utils import setup_module_logging, get_bool

logger = logging.Logger(__name__)

"""
Classifications are assigned to dimensions using the chart and table builder
"""


class DimensionClassificationService:
    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config["LOG_LEVEL"])
        self.logger.info("Initialised classification linker service")

    @staticmethod
    def set_chart_classification_on_dimension(classification_link, dimension):
        pass

    @staticmethod
    def set_table_classification_on_dimension(classification_link, dimension):
        pass

    @staticmethod
    def set_dimension_classification_manually(classification_link, dimension):
        pass

    @staticmethod
    def get_dimension_classification_link(dimension, family):
        pass


class DimensionClassificationLink:
    def __init__(self, chart_link, table_link):
        self.chart_link = chart_link
        self.table_link = table_link
        self.dimension_link = self.get_dimension_link()

    @staticmethod
    def from_database_object(dimension_categorisation):
        pass

    def get_dimension_link(self):
        return None

    def get_dimension_categorisation(self, dimension):
        pass


class ClassificationLink:
    def __init__(self, classification_id, includes_parents=False, includes_all=False, includes_unknown=False):
        self.classification_id = classification_id
        self.includes_parents = includes_parents
        self.includes_all = includes_all
        self.includes_unknown = includes_unknown


dimension_classification_service = DimensionClassificationService()

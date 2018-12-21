import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import ClassificationNotFoundException

from application.cms.models import Classification, Ethnicity, DimensionClassification

from application.utils import setup_module_logging, get_bool

logger = logging.Logger(__name__)

"""
The classification service is in charge of management for ethnicity classifications and values

Classifications
ClassificationValues

which chain together in many-to-many relationships

"""


class ClassificationService:
    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config["LOG_LEVEL"])
        self.logger.info("Initialised classification service")

    """
    CLASSIFICATION Management
    """

    def create_classification(self, id_str, subfamily, title, position=999, long_title=None):
        classification_long_title = title if long_title is None else long_title

        try:
            classification = self.get_classification_by_id(id_str)
        except ClassificationNotFoundException as e:
            classification = Classification(
                id=id_str, title=title, subfamily=subfamily, long_title=classification_long_title, position=position
            )

            db.session.add(classification)
            db.session.commit()

        return classification

    def create_classification_with_values(
        self, id_str, subfamily, title, long_title=None, position=999, values=[], values_as_parent=[]
    ):
        classification = self.create_classification(id_str, subfamily, title, position, long_title)

        self.add_values_to_classification(classification, values)
        self.add_values_to_classification_as_parents(classification, values_as_parent)

        return classification

    def update_classification(self, classification):
        db.session.add(classification)
        db.session.commit()

    def delete_classification(self, classification):
        self.delete_unused_values_from_database(classification)
        db.session.delete(classification)
        db.session.commit()

    def delete_unused_values_from_database(self, classification):
        if DimensionClassification.query.filter_by(classification_id=classification.id).count() == 0:
            self.remove_classification_values(classification)

    @staticmethod
    def get_classification_by_id(classification_id):
        try:
            return Classification.query.filter_by(id=classification_id).one()
        except NoResultFound as e:
            raise ClassificationNotFoundException("Classification with id %s not found" % classification_id)

    @staticmethod
    def get_all_classifications():
        return Classification.query.all()

    @staticmethod
    def edit_classification(classification, subfamily_update, title_update, position_update):
        classification.subfamily = subfamily_update
        classification.title = title_update
        classification.position = position_update
        db.session.commit()

    """
    VALUE management
    """

    @staticmethod
    def get_value(value):
        return Ethnicity.query.filter_by(value=value).first()

    @staticmethod
    def get_all_values():
        values = Ethnicity.query.all()
        return [v.value for v in values]

    @staticmethod
    def get_value_by_slug(slug):
        from slugify import slugify

        value_list = [v for v in Ethnicity.query.all() if slugify(v.value) == slug]
        return value_list[0] if len(value_list) > 0 else None

    @staticmethod
    def get_all_classification_values():
        return Ethnicity.query.all()

    def get_or_create_value(self, value_string, position=999):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            return classification_value
        else:
            classification_value = Ethnicity(value=value_string, position=position)
            db.session.add(classification_value)
            db.session.commit()
            return classification_value

    def update_value_position(self, value_string, value_position):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            classification_value.position = value_position
            db.session.commit()
            return classification_value
        return None

    @staticmethod
    def clean_value_database():
        values = Ethnicity.query.all()
        for value in values:
            if len(value.classifications) == 0:
                db.session.delete(value)
                db.session.commit()

    """
    CATEGORY >-< VALUE relationship management
    """

    def add_value_to_classification(self, classification, value_title):
        value = self.get_or_create_value(value_string=value_title)
        classification.ethnicities.append(value)

        db.session.commit()
        return classification

    def add_value_to_classification_as_parent(self, classification, value_string):
        value = self.get_or_create_value(value_string=value_string)
        classification.parent_values.append(value)

        db.session.commit()
        return classification

    def add_values_to_classification(self, classification, value_strings):
        for value_string in value_strings:
            value = self.get_or_create_value(value_string=value_string)
            classification.ethnicities.append(value)
        db.session.commit()
        return classification

    def add_values_to_classification_as_parents(self, classification, value_strings):
        for value_string in value_strings:
            value = self.get_or_create_value(value_string=value_string)
            classification.parent_values.append(value)
        db.session.commit()
        return classification

    def remove_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.ethnicities.remove(value)
        db.session.commit()

    def remove_parent_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.parent_values.remove(value)
        db.session.commit()

    @staticmethod
    def remove_classification_values(classification):
        for value in classification.ethnicities:
            db.session.delete(value)
        db.session.commit()

    @staticmethod
    def remove_parent_classification_values(classification):
        for value in classification.parent_values:
            db.session.delete(value)
        db.session.commit()


class ClassificationWithIncludesParentsAllUnknown:
    def __init__(self, classification_id, includes_parents=False, includes_all=False, includes_unknown=False):
        self.classification_id = classification_id
        self.includes_parents = includes_parents
        self.includes_all = includes_all
        self.includes_unknown = includes_unknown


classification_service = ClassificationService()

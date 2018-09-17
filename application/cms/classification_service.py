import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import ClassificationNotFoundException

from application.cms.models import Page, Dimension, Categorisation, CategorisationValue, DimensionCategorisation

from application.utils import setup_module_logging, get_bool

logger = logging.Logger(__name__)

"""
The classification service is in charge of all CRUD for classifications and values

Classifications
ClassificationValues
&
ClassificationCategories

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

    def create_classification(self, code, family, subfamily, title, position=999):
        try:
            classification = self.get_classification_by_title(family, title)
        except ClassificationNotFoundException as e:
            classification = Categorisation(
                code=code, title=title, family=family, subfamily=subfamily, position=position
            )
            db.session.add(classification)
            db.session.commit()
        return classification

    def create_classification_with_values(
        self, code, family, subfamily, title, position=999, values=[], values_as_parent=[]
    ):
        classification = self.create_classification(code, family, subfamily, title, position)
        self.add_values_to_classification(classification, values)
        self.add_values_to_classification_as_parents(classification, values_as_parent)

        return classification

    def delete_classification(self, classification):
        self.delete_unused_values_from_database(classification)
        db.session.delete(classification)
        db.session.commit()

    def delete_unused_values_from_database(self, classification):
        if DimensionCategorisation.query.filter_by(categorisation_id=classification.id).count() == 0:
            self.remove_classification_values(classification)

    @staticmethod
    def get_classification_by_code(code):
        try:
            return Categorisation.query.filter_by(code=code).one()
        except NoResultFound as e:
            raise ClassificationNotFoundException("Categorisation %s not found" % code)

    @staticmethod
    def get_classification_by_title(family, title):
        try:
            return Categorisation.query.filter_by(title=title, family=family).one()
        except NoResultFound as e:
            raise ClassificationNotFoundException("Classification %s not found in family %s" % (title, family))

    @staticmethod
    def get_classification_by_id(classification_id):
        try:
            return Categorisation.query.get(classification_id)
        except NoResultFound as e:
            raise ClassificationNotFoundException("Categorisation with id %s not found" % classification_id)

    @staticmethod
    def get_all_classifications():
        return Categorisation.query.all()

    @staticmethod
    def get_ethnicity_classifications():
        return ClassificationService.get_classifications_by_family("Ethnicity")

    @staticmethod
    def get_classifications_by_family(family):
        classifications = Categorisation.query.filter_by(family=family)

        # get a list of unique subfamilies
        subfamilies = list(set([classification.subfamily for classification in classifications]))
        subfamilies.sort()

        # get a list of categories for each subfamily
        results = []
        for subfamily in subfamilies:
            results = results + [
                {
                    "subfamily": subfamily,
                    "categorisation": Categorisation.query.filter_by(family=family, subfamily=subfamily).order_by(
                        Categorisation.position
                    ),
                }
            ]
        return results

    @staticmethod
    def edit_classification(classification, family_update, subfamily_update, title_update, position_update):
        classification.family = family_update
        classification.subfamily = subfamily_update
        classification.title = title_update
        classification.position = position_update
        db.session.add(classification)
        db.session.commit()

    """
    CATEGORY >-< DIMENSION relationship management
    """

    @staticmethod
    def link_classification_to_dimension(dimension, classification_link):
        try:
            return ClassificationService._update_dimension_classification_link(classification_link, dimension)
        except NoResultFound:
            return ClassificationService._create_new_dimension_classification_link(
                classification_link, dimension)

    @staticmethod
    def _update_dimension_classification_link(classification_link, dimension):
        classification = ClassificationService.get_classification_by_code(classification_link.code)
        dimension_categorisation = DimensionCategorisation.query.filter_by(
            dimension_guid=dimension.guid, categorisation_id=classification.id
        ).one()
        dimension_categorisation.includes_parents = classification_link.includes_parents
        dimension_categorisation.includes_all = classification_link.includes_all
        dimension_categorisation.includes_unknown = classification_link.includes_unknown
        db.session.add(dimension_categorisation)
        db.session.commit()

    @staticmethod
    def _create_new_dimension_classification_link(classification_link, dimension):
        classification = ClassificationService.get_classification_by_code(classification_link.code)
        dimension_categorisation = DimensionCategorisation(
            dimension_guid=dimension.guid,
            categorisation_id=classification.id,
            includes_parents=classification_link.includes_parents,
            includes_all=classification_link.includes_all,
            includes_unknown=classification_link.includes_unknown,
        )
        dimension.categorisation_links.append(dimension_categorisation)
        db.session.add(dimension)
        classification.dimension_links.append(dimension_categorisation)
        db.session.add(classification)
        db.session.commit()
        return dimension_categorisation

    @staticmethod
    def unlink_classification_from_dimension(dimension, classification):
        try:
            link = DimensionCategorisation.query.filter_by(
                categorisation_id=classification.id, dimension_guid=dimension.guid
            ).first()

            db.session.delete(link)
            db.session.commit()
        except NoResultFound:
            print(
                "could not find link between dimension %s and classification %s" % (dimension.id, classification.code)
            )

    @staticmethod
    def get_classification_link_for_dimension_by_family(dimension, family):
        for link in dimension.categorisation_links:
            if link.categorisation.family == family:
                return link
        return None

    @staticmethod
    def unlink_dimension_from_family(dimension, family):
        for link in dimension.categorisation_links:
            if link.classification.family == family:
                db.session.delete(link)
        db.session.commit()

    """
    VALUE management
    """

    @staticmethod
    def get_value(value):
        return CategorisationValue.query.filter_by(value=value).first()

    @staticmethod
    def get_all_values():
        values = CategorisationValue.query.all()
        return [v.value for v in values]

    @staticmethod
    def get_value_by_uri(uri):
        from slugify import slugify

        value_list = [v for v in CategorisationValue.query.all() if slugify(v.value) == uri]
        return value_list[0] if len(value_list) > 0 else None

    @staticmethod
    def get_all_classification_values():
        return CategorisationValue.query.all()

    def create_value(self, value_string, position=999):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            return classification_value
        else:
            classification_value = CategorisationValue(value=value_string, position=position)
            db.session.add(classification_value)
            db.session.commit()
            return classification_value

    def create_or_get_value(self, value_string, position=999):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            return classification_value
        else:
            return self.create_value(value_string=value_string, position=position)

    def update_value_position(self, value_string, value_position):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            classification_value.position = value_position
            db.session.add(classification_value)
            db.session.commit()
            return classification_value
        return None

    @staticmethod
    def clean_value_database():
        values = CategorisationValue.query.all()
        for value in values:
            if len(value.categorisations) == 0:
                db.session.delete(value)
                db.session.commit()

    """
    CATEGORY >-< VALUE relationship management
    """

    def add_value_to_classification(self, classification, value_title):
        value = self.create_or_get_value(value_string=value_title)
        classification.values.append(value)

        db.session.add(classification)
        db.session.commit()
        return classification

    def add_value_to_classification_as_parent(self, classification, value_string):
        value = self.create_or_get_value(value_string=value_string)
        classification.parent_values.append(value)

        db.session.add(classification)
        db.session.commit()
        return classification

    def add_values_to_classification(self, classification, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            classification.values.append(value)
        db.session.add(classification)
        db.session.commit()
        return classification

    def add_values_to_classification_as_parents(self, classification, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            classification.parent_values.append(value)
        db.session.add(classification)
        db.session.commit()
        return classification

    def remove_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.values.remove(value)
        db.session.add(classification)
        db.session.commit()

    def remove_parent_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.parent_values.remove(value)
        db.session.add(classification)
        db.session.commit()

    @staticmethod
    def remove_classification_values(classification):
        for value in classification.values:
            db.session.delete(value)
        db.session.commit()

    @staticmethod
    def remove_parent_classification_values(classification):
        for value in classification.parent_values:
            db.session.delete(value)
        db.session.commit()


class ClassificationsSynchroniser:
    def __init__(self, classification_service):
        self.classification_service = classification_service

    def synchronise_values_from_file(self, file_name):
        import csv

        with open(file_name, "r") as f:
            reader = csv.reader(f)
            classification_value_list = list(reader)[1:]

        # pick contents of the file
        classification_ids_in_file = list(set([row[0] for row in classification_value_list]))
        unique_values = {row[1]: row[3] for row in classification_value_list}

        # pull off existing values
        for code in classification_ids_in_file:
            classification = self.classification_service.get_classification_by_code(code)
            self.classification_service.remove_classification_values(classification)
        self.classification_service.clean_value_database()

        for value in unique_values:
            self.classification_service.create_value(value, unique_values[value])

        # next import the rows
        for value_row in classification_value_list:
            parent_type = value_row[2].strip().lower()
            classification = self.classification_service.get_classification_by_code(value_row[0])

            if parent_type == "both":
                classification_service.add_value_to_classification(
                    classification=classification, value_title=value_row[1]
                )
                classification_service.add_value_to_classification_as_parent(
                    classification=classification, value_string=value_row[1]
                )

            elif parent_type == "only":
                classification_service.add_value_to_classification_as_parent(
                    classification=classification, value_string=value_row[1]
                )

            else:
                classification_service.add_value_to_classification(
                    classification=classification, value_title=value_row[1]
                )

        print(
            "Value import complete: Assigned %d unique values to %d categories in %d assignments"
            % (len(unique_values), len(classification_ids_in_file), len(classification_value_list))
        )

    def synchronise_classification_from_file(self, file_name):
        import csv

        with open(file_name, "r") as f:
            reader = csv.reader(f)
            classification_list = list(reader)[1:]

        synced = 0
        created = 0

        for position, classification_row in enumerate(classification_list):
            code = classification_row[0]
            family = "Ethnicity"
            subfamily = classification_row[1]
            title = classification_row[2]
            has_parents = classification_row[3]

            try:
                classification = self.classification_service.get_classification_by_code(code)
                classification.subfamily = subfamily
                classification.title = title
                classification.position = position
                synced += 1
            except ClassificationNotFoundException as e:
                classification = self.classification_service.create_classification(
                    code, family, subfamily, title, position
                )
                created += 1

            self.classification_service.remove_parent_classification_values(classification)
            if has_parents == "TRUE":
                self.classification_service.add_value_to_category_as_parent(classification, "parent")
        print("Category import complete: Created %d new. Synchronised %d" % (created, synced))

    def import_dimension_categorisations(self, header_row, data_rows):
        try:
            guid_column = header_row.index("dimension_guid")
            categorisation_column = header_row.index("categorisation_code")
            has_parent_column = header_row.index("has_parent")
            has_all_column = header_row.index("has_all")
            has_unknown_column = header_row.index("has_unknown")

            for row in data_rows:
                try:
                    # get values
                    dimension = Dimension.query.filter_by(guid=row[guid_column]).one()
                    classification = self.classification_service.get_categorisation_by_code(
                        categorisation_code=row[categorisation_column]
                    )
                    has_parent = get_bool(row[has_parent_column])
                    has_all = get_bool(row[has_all_column])
                    has_unknown = get_bool(row[has_unknown_column])

                    self.classification_service.link_classification_to_dimension(
                        dimension=dimension,
                        classification=classification,
                        includes_parents=has_parent,
                        includes_all=has_all,
                        includes_unknown=has_unknown,
                    )

                except NoResultFound as e:
                    print("Could not find dimension with guid:%s" % row[guid_column])

                except ClassificationNotFoundException as e:
                    print("Could not find classification with code:%s" % row[categorisation_column])

        except ValueError as e:
            self.classification_service.logger.exception(e)
            print("Columns required dimension_guid, categorisation_code, has_parents, has_all, has_unknown")

    def import_dimension_categorisations_from_file(self, file_name):
        import csv

        with open(file_name, "r") as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        header_row = all_rows[0]
        data_rows = all_rows[1:]
        print(header_row)
        self.import_dimension_categorisations(header_row=header_row, data_rows=data_rows)


class ClassificationLink:
    def __init__(self, classification_id, includes_parents=False, includes_all=False, includes_unknown=False):
        self.classification_id = classification_id
        self.includes_parents = includes_parents
        self.includes_all = includes_all
        self.includes_unknown = includes_unknown


classification_service = ClassificationService()

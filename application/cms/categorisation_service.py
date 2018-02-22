import logging

from application import db

from application.cms.models import (
    Page,
    Dimension,
    Categorisation,
    CategorisationValue,
    DimensionCategorisation)

from application.utils import setup_module_logging

logger = logging.Logger(__name__)

'''
The category service is in charge of all CRUD for categories and values

Categories
CategoryValues
&
DimensionCategories

which chain together in many-to-many relationships

'''


class CategorisationService:

    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised category service')

    def synchronise_values_from_file(self, file_name):
        import csv
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            categorisation_value_list = list(reader)[1:]

        # pick contents of the file
        categorisation_ids_in_file = list(set([row[0] for row in categorisation_value_list]))

        # pull off existing values
        for code in categorisation_ids_in_file:
            category = self.get_categorisation_by_code(categorisation_code=code)
            self._remove_categorisation_values(category=category)
        self.clean_value_database()

        # next import the rows
        for value_row in categorisation_value_list:
            parent_type = value_row[2].strip().lower()
            categorisation = self.get_categorisation_by_code(categorisation_code=value_row[0])

            if parent_type == 'both':
                self.add_value_to_categorisation(category=category, value_title=value_row[1])
                self.add_value_to_category_as_parent(categorisation=categorisation, value_string=value_row[1])

            elif parent_type == 'only':
                self.add_value_to_category_as_parent(categorisation=categorisation, value_string=value_row[1])

            else:
                self.add_value_to_categorisation(category=category, value_title=value_row[1])

    def synchronise_categorisations_from_file(self, file_name):
        import csv
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            categorisation_list = list(reader)[1:]

        for position, categorisation_row in enumerate(categorisation_list):
            code = categorisation_row[0]
            family = 'Ethnicity'
            subfamily = categorisation_row[1]
            title = categorisation_row[2]
            has_parents = categorisation_row[3]

            categorisation = self.get_categorisation_by_code(categorisation_code=code)
            if categorisation:
                categorisation.subfamily = subfamily
                categorisation.title = title
                categorisation.position = position
            else:
                categorisation = self.create_categorisation(code, family, subfamily, title, position)

            self._remove_parent_categorisation_values(categorisation)
            if has_parents == 'TRUE':
                self.add_value_to_category_as_parent(categorisation, 'parent')

    '''
    CATEGORY Management
    '''

    def create_categorisation(self, code, family, subfamily, title, position=999):
        category = Categorisation(code=code, title=title, family=family, subfamily=subfamily, position=position)
        db.session.add(category)
        db.session.commit()
        return category

    def create_categorisation_with_values(self, code, family, subfamily, title, position=999, values=[],
                                          values_as_parent=[]):
        categorisation = Categorisation(code=code, title=title, family=family, subfamily=subfamily, position=position)
        db.session.add(categorisation)
        db.session.commit()

        self.add_values_to_categorisation(categorisation, values)
        self.add_values_to_categorisation_as_parents(categorisation, values_as_parent)

        return categorisation

    def delete_categorisation(self, categorisation):
        if DimensionCategorisation.query.filter_by(categorisation_id=categorisation.id).count() == 0:
            self._remove_categorisation_values(categorisation)
        db.session.delete(categorisation)
        db.session.commit()

    def get_categorisation(self, family, title):
        return Categorisation.query.filter_by(title=title, family=family).first()

    def get_categorisation_by_id(self, categorisation_id):
        return Categorisation.query.filter_by(id=categorisation_id).first()

    def get_categorisation_by_code(self, categorisation_code):
        return Categorisation.query.filter_by(code=categorisation_code).first()

    def get_all_categorisations(self):
        categories = Categorisation.query.all()
        return categories

    def get_categorisations_by_family(self, family):
        categorisations = Categorisation.query.filter_by(family=family)

        # get a list of unique subfamilies
        subfamilies = list(set([categorisation.subfamily for categorisation in categorisations]))
        subfamilies.sort()

        # get a list of categories for each subfamily
        results = []
        for subfamily in subfamilies:
            results = results + [{
                'subfamily': subfamily,
                'categorisations': Categorisation.query.filter_by(family=family,
                                                                  subfamily=subfamily).order_by(Categorisation.position)
            }]
        return results

    def edit_categorisation(self, categorisation, family_update, subfamily_update, title_update, position_update):
        categorisation.family = family_update
        categorisation.subfamily = subfamily_update
        categorisation.title = title_update
        categorisation.position = position_update
        db.session.add(categorisation)
        db.session.commit()

    '''
    CATEGORY >-< DIMENSION relationship management
    '''

    def link_categorisation_to_dimension(self, dimension, categorisation,
                                         includes_parents, includes_all, includes_unknown):

        db_dimension_categorisation = DimensionCategorisation(dimension_guid=dimension.guid,
                                                              categorisation_id=categorisation.id,
                                                              includes_parents=includes_parents,
                                                              includes_all=includes_all,
                                                              includes_unknown=includes_unknown)

        dimension.categorisation_links.append(db_dimension_categorisation)
        db.session.add(dimension)
        categorisation.dimension_links.append(db_dimension_categorisation)
        db.session.add(categorisation)
        db.session.commit()
        return db_dimension_categorisation

    def unlink_categorisation_from_dimension(self, dimension, categorisation):
        link = DimensionCategorisation.query.filter_by(categorisation_id=categorisation.id,
                                                       dimension_guid=dimension.guid).first()

        db.session.delete(link)
        db.session.commit()

    def get_categorisation_link_for_dimension_by_family(self, dimension, family):
        for link in dimension.categorisation_links:
            if link.categorisation.family == family:
                return link
        return None

    def unlink_dimension_from_family(self, dimension, family):
        for link in dimension.categorisation_links:
            if link.categorisation.family == family:
                db.session.delete(link)
        db.session.commit()

    '''
    VALUE management
    '''

    def get_value(self, value):
        return CategorisationValue.query.filter_by(value=value).first()

    def get_all_values(self):
        values = CategorisationValue.query.all()
        return [v.value for v in values]

    def create_value(self, value_string):
        category_value = self.get_value(value=value_string)
        if category_value:
            return category_value
        else:
            category_value = CategorisationValue(value=value_string)
            db.session.add(category_value)
            db.session.commit()
            return category_value

    def create_or_get_value(self, value_string):
        category_value = self.get_value(value=value_string)
        if category_value:
            return category_value
        else:
            return self.create_value(value_string=value_string)

    def clean_value_database(self):
        values = CategorisationValue.query.all()
        for value in values:
            if len(value.categorisations) == 0:
                db.session.delete(value)
                db.session.commit()

    '''
    CATEGORY >-< VALUE relationship management
    '''

    def add_value_to_categorisation(self, category, value_title):
        value = self.create_or_get_value(value_string=value_title)
        category.values.append(value)

        db.session.add(category)
        db.session.commit()
        return category

    def add_value_to_category_as_parent(self, categorisation, value_string):
        value = self.create_or_get_value(value_string=value_string)
        categorisation.parent_values.append(value)

        db.session.add(categorisation)
        db.session.commit()
        return categorisation

    def add_values_to_categorisation(self, categorisation, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            categorisation.values.append(value)
        db.session.add(categorisation)
        db.session.commit()
        return categorisation

    def add_values_to_categorisation_as_parents(self, category, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            category.parent_values.append(value)
        db.session.add(category)
        db.session.commit()
        return category

    def remove_value_from_categorisation(self, categorisation, value_string):
        value = self.get_value(value=value_string)

        categorisation.values.remove(value)
        db.session.add(categorisation)
        db.session.commit()

    def remove_parent_value_from_categorisation(self, category, value_string):
        value = self.get_value(value=value_string)

        category.parent_values.remove(value)
        db.session.add(category)
        db.session.commit()

    def _remove_categorisation_values(self, category):
        for value in category.values:
            db.session.delete(value)
        db.session.commit()

    def _remove_parent_categorisation_values(self, category):
        for value in category.parent_values:
            db.session.delete(value)
        db.session.commit()


categorisation_service = CategorisationService()

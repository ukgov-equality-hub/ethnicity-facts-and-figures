import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import CategorisationNotFoundException

from application.cms.models import (
    Page,
    Dimension,
    Categorisation,
    CategorisationValue,
    DimensionCategorisation
)

from application.utils import setup_module_logging, get_bool

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
        unique_values = {row[1]: row[3] for row in categorisation_value_list}

        # pull off existing values
        for code in categorisation_ids_in_file:
            category = self.get_categorisation_by_code(categorisation_code=code)
            self._remove_categorisation_values(category=category)
        self.clean_value_database()

        for value in unique_values:
            categorisation_service.create_value(value, unique_values[value])

        # next import the rows
        for value_row in categorisation_value_list:
            parent_type = value_row[2].strip().lower()
            categorisation = self.get_categorisation_by_code(categorisation_code=value_row[0])

            if parent_type == 'both':
                self.add_value_to_categorisation(categorisation=categorisation, value_title=value_row[1])
                self.add_value_to_category_as_parent(categorisation=categorisation, value_string=value_row[1])

            elif parent_type == 'only':
                self.add_value_to_category_as_parent(categorisation=categorisation, value_string=value_row[1])

            else:
                self.add_value_to_categorisation(categorisation=categorisation, value_title=value_row[1])

        print('Value import complete: Assigned %d unique values to %d categories in %d assignments' % (
            len(unique_values), len(categorisation_ids_in_file), len(categorisation_value_list)
        ))

    def synchronise_categorisations_from_file(self, file_name):
        import csv
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            categorisation_list = list(reader)[1:]

        synced = 0
        created = 0

        for position, categorisation_row in enumerate(categorisation_list):
            code = categorisation_row[0]
            family = 'Ethnicity'
            subfamily = categorisation_row[1]
            title = categorisation_row[2]
            has_parents = categorisation_row[3]

            try:
                categorisation = self.get_categorisation_by_code(categorisation_code=code)
                categorisation.subfamily = subfamily
                categorisation.title = title
                categorisation.position = position
                synced += 1
            except CategorisationNotFoundException as e:
                categorisation = self.create_categorisation(code, family, subfamily, title, position)
                created += 1

            self._remove_parent_categorisation_values(categorisation)
            if has_parents == 'TRUE':
                self.add_value_to_category_as_parent(categorisation, 'parent')

        print('Category import complete: Created %d new. Synchronised %d' % (created, synced))

    '''
    CATEGORY Management
    '''

    def create_categorisation(self, code, family, subfamily, title, position=999):
        try:
            category = self.get_categorisation(family, title)
        except CategorisationNotFoundException as e:
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

    @staticmethod
    def get_categorisation(family, title):
        try:
            return Categorisation.query.filter_by(title=title, family=family).one()
        except NoResultFound as e:
            raise CategorisationNotFoundException("Categorisation %s not found in family %s" % (title, family))

    @staticmethod
    def get_categorisation_by_id(categorisation_id):
        try:
            return Categorisation.query.get(id=categorisation_id)
        except NoResultFound as e:
            raise CategorisationNotFoundException("Categorisation with id %s not found" % categorisation_id)

    @staticmethod
    def get_categorisation_by_code(categorisation_code):
        try:
            return Categorisation.query.filter_by(code=categorisation_code).one()
        except NoResultFound as e:
            raise CategorisationNotFoundException("Categorisation with code %s not found" % categorisation_code)

    @staticmethod
    def get_all_categorisations():
        return Categorisation.query.all()

    @staticmethod
    def get_all_categorisations_with_counts():
        import sqlalchemy as sa
        from application import db

        query = db.session.query(
                Categorisation.title.label('title'),
                sa.func.count(sa.func.distinct(DimensionCategorisation.dimension_guid)).label('dimension_count'),
                sa.func.count(sa.func.distinct(Dimension.page_id)).label('measure_count'),
                sa.func.sum(
                    sa.case([
                        (DimensionCategorisation.includes_all == sa.text('TRUE'), 1)
                        ],
                        else_=0
                    )
                ).label('includes_all_count'),
                sa.func.sum(
                    sa.case([
                        (DimensionCategorisation.includes_parents == sa.text('TRUE'), 1)
                        ],
                        else_=0
                    )
                ).label('includes_parents_count'),
                sa.func.sum(
                    sa.case([
                        (DimensionCategorisation.includes_unknown == sa.text('TRUE'), 1)
                        ],
                        else_=0
                    )
                ).label('includes_unknown_count'),
            ).join(DimensionCategorisation) \
            .join(Dimension) \
            .join(Page)\
            .filter(Page.latest == sa.text('TRUE'))\
            .order_by(Categorisation.id)\
            .group_by(Categorisation.id)

        return query

    @staticmethod
    def get_categorisations_by_family(family):
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

    @staticmethod
    def edit_categorisation(categorisation, family_update, subfamily_update, title_update, position_update):
        categorisation.family = family_update
        categorisation.subfamily = subfamily_update
        categorisation.title = title_update
        categorisation.position = position_update
        db.session.add(categorisation)
        db.session.commit()

    '''
    CATEGORY >-< DIMENSION relationship management
    '''

    @staticmethod
    def link_categorisation_to_dimension(dimension, categorisation,
                                         includes_parents, includes_all, includes_unknown):

        try:
            dimension_categorisation = DimensionCategorisation \
                .query.filter_by(dimension_guid=dimension.guid,
                                 categorisation_id=categorisation.id).one()

            dimension_categorisation.includes_parents = includes_parents
            dimension_categorisation.includes_all = includes_all
            dimension_categorisation.includes_unknown = includes_unknown
            db.session.add(dimension_categorisation)
        except NoResultFound:
            dimension_categorisation = DimensionCategorisation(dimension_guid=dimension.guid,
                                                               categorisation_id=categorisation.id,
                                                               includes_parents=includes_parents,
                                                               includes_all=includes_all,
                                                               includes_unknown=includes_unknown)
            dimension.categorisation_links.append(dimension_categorisation)
            db.session.add(dimension)
            categorisation.dimension_links.append(dimension_categorisation)
            db.session.add(categorisation)

        db.session.commit()
        return dimension_categorisation

    @staticmethod
    def unlink_categorisation_from_dimension(dimension, categorisation):
        try:
            link = DimensionCategorisation.query.filter_by(categorisation_id=categorisation.id,
                                                           dimension_guid=dimension.guid).first()

            db.session.delete(link)
            db.session.commit()
        except NoResultFound:
            print(
                "could not find link between dimension %s and categorisation %s" % (dimension.id, categorisation.code))

    @staticmethod
    def get_categorisation_link_for_dimension_by_family(dimension, family):
        for link in dimension.categorisation_links:
            if link.categorisation.family == family:
                return link
        return None

    @staticmethod
    def unlink_dimension_from_family(dimension, family):
        for link in dimension.categorisation_links:
            if link.categorisation.family == family:
                db.session.delete(link)
        db.session.commit()

    def import_dimension_categorisations(self, header_row, data_rows):
        try:
            guid_column = header_row.index('dimension_guid')
            categorisation_column = header_row.index('categorisation_code')
            has_parent_column = header_row.index('has_parent')
            has_all_column = header_row.index('has_all')
            has_unknown_column = header_row.index('has_unknown')

            for row in data_rows:
                try:
                    # get values
                    dimension = Dimension.query.filter_by(guid=row[guid_column]).one()
                    categorisation = self.get_categorisation_by_code(categorisation_code=row[categorisation_column])
                    has_parent = get_bool(row[has_parent_column])
                    has_all = get_bool(row[has_all_column])
                    has_unknown = get_bool(row[has_unknown_column])

                    self.link_categorisation_to_dimension(dimension=dimension,
                                                          categorisation=categorisation,
                                                          includes_parents=has_parent,
                                                          includes_all=has_all,
                                                          includes_unknown=has_unknown)

                except NoResultFound as e:
                    print('Could not find dimension with guid:%s' % row[guid_column])

                except CategorisationNotFoundException as e:
                    print('Could not find categorisation with code:%s' % row[categorisation_column])

        except ValueError as e:
            self.logger.exception(e)
            print('Columns required dimension_guid, categorisation_code, has_parents, has_all, has_unknown')

    def import_dimension_categorisations_from_file(self, file_name):
        import csv
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            all_rows = list(reader)

        header_row = all_rows[0]
        data_rows = all_rows[1:]
        print(header_row)
        self.import_dimension_categorisations(header_row=header_row, data_rows=data_rows)

    '''
    VALUE management
    '''

    @staticmethod
    def get_value(value):
        return CategorisationValue.query.filter_by(value=value).first()

    @staticmethod
    def get_all_values():
        values = CategorisationValue.query.all()
        return [v.value for v in values]

    @staticmethod
    def get_all_categorisation_values():
        return CategorisationValue.query.all()

    def create_value(self, value_string, position=999):
        category_value = self.get_value(value=value_string)
        if category_value:
            return category_value
        else:
            category_value = CategorisationValue(value=value_string, position=position)
            db.session.add(category_value)
            db.session.commit()
            return category_value

    def create_or_get_value(self, value_string, position=999):
        category_value = self.get_value(value=value_string)
        if category_value:
            return category_value
        else:
            return self.create_value(value_string=value_string, position=position)

    def update_value_position(self, value_string, value_position):
        category_value = self.get_value(value=value_string)
        if category_value:
            category_value.position = value_position
            db.session.add(category_value)
            db.session.commit()
            return category_value
        return None

    @staticmethod
    def clean_value_database():
        values = CategorisationValue.query.all()
        for value in values:
            if len(value.categorisations) == 0:
                db.session.delete(value)
                db.session.commit()

    '''
    CATEGORY >-< VALUE relationship management
    '''

    def add_value_to_categorisation(self, categorisation, value_title):
        value = self.create_or_get_value(value_string=value_title)
        categorisation.values.append(value)

        db.session.add(categorisation)
        db.session.commit()
        return categorisation

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

    @staticmethod
    def _remove_categorisation_values(category):
        for value in category.values:
            db.session.delete(value)
        db.session.commit()

    @staticmethod
    def _remove_parent_categorisation_values(category):
        for value in category.parent_values:
            db.session.delete(value)
        db.session.commit()


categorisation_service = CategorisationService()

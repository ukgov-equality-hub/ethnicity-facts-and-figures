from sqlalchemy import null
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.categorisation_service import categorisation_service
from application.cms.exceptions import DimensionNotFoundException, DimensionAlreadyExists, PageUnEditable
from application.cms.models import Dimension
from application.cms.service import Service
from application.utils import create_guid


class DimensionService(Service):

    def __init__(self):
        super().__init__()

    def create_dimension(self, page, title, time_period, summary, ethnicity_category, include_parents=False,
                         include_all=False, include_unknown=False):

        guid = create_guid(title)

        if not self.check_dimension_title_unique(page, title):
            raise DimensionAlreadyExists()
        else:
            self.logger.info('Dimension with guid %s does not exist ok to proceed', guid)

            db_dimension = Dimension(guid=guid,
                                     title=title,
                                     time_period=time_period,
                                     summary=summary,
                                     page=page,
                                     position=page.dimensions.count())

            page.dimensions.append(db_dimension)
            db.session.add(page)
            db.session.commit()

            if ethnicity_category and ethnicity_category != '':
                category = categorisation_service.get_categorisation_by_id(ethnicity_category)
                categorisation_service.link_categorisation_to_dimension(db_dimension,
                                                                        category,
                                                                        include_parents,
                                                                        include_all,
                                                                        include_unknown)

            return page.get_dimension(db_dimension.guid)

    # TODO can this roll up into update dimension?
    def update_measure_dimension(self, dimension, post_data):
        data = {}
        if 'chartObject' in post_data:
            data['chart'] = post_data['chartObject']

            if 'chartBuilderVersion' in post_data and post_data['chartBuilderVersion'] > 1:
                data['chart_2_source_data'] = post_data['source']
                data['chart_builder_version'] = 2
            else:
                data['chart_source_data'] = post_data['source']
                data['chart_builder_version'] = 1

        if 'tableObject' in post_data:
            data['table'] = post_data['tableObject']
            data['table_source_data'] = post_data['source']

        self.update_dimension(dimension, data)

    def set_dimension_positions(self, dimension_positions):
        for item in dimension_positions:
            try:
                dimension = Dimension.query.filter_by(guid=item['guid']).one()
                dimension.position = item['index']
                db.session.add(dimension)
            except NoResultFound as e:
                self.logger.exception(e)
                raise DimensionNotFoundException()
        if db.session.dirty:
            db.session.commit()

    def delete_dimension(self, page, guid):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        dimension = page.get_dimension(guid)

        db.session.delete(dimension)
        db.session.commit()

    @staticmethod
    def get_dimension_with_guid(guid):
        try:
            return Dimension.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            raise DimensionNotFoundException()

    @staticmethod
    def delete_chart(dimension):
        dimension.chart = null()
        dimension.chart_source_data = null()
        db.session.add(dimension)
        db.session.commit()

    @staticmethod
    def delete_table(dimension):
        dimension.table = null()
        dimension.table_source_data = null()
        db.session.add(dimension)
        db.session.commit()

    @staticmethod
    def check_dimension_title_unique(page, title):
        try:
            Dimension.query.filter_by(page=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    @staticmethod
    def update_dimension(dimension, data):
        dimension.title = data['title'] if 'title' in data else dimension.title
        dimension.time_period = data['time_period'] if 'time_period' in data else dimension.time_period
        dimension.summary = data['summary'] if 'summary' in data else dimension.summary
        dimension.chart = data['chart'] if 'chart' in data else dimension.chart
        dimension.table = data['table'] if 'table' in data else dimension.table
        dimension.chart_builder_version = data[
            'chart_builder_version'] if 'chart_builder_version' in data else dimension.chart_builder_version

        if dimension.chart and data.get('chart_source_data') is not None:
            chart_options = data.get('chart_source_data').get('chartOptions')
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = '[None]'
            data['chart_source_data']['chartOptions'] = chart_options
            dimension.chart_source_data = data.get('chart_source_data')

        if dimension.chart and data.get('chart_2_source_data') is not None:
            chart_options = data.get('chart_2_source_data').get('chartOptions')
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = '[None]'
            data['chart_2_source_data']['chartOptions'] = chart_options
            dimension.chart_2_source_data = data.get('chart_2_source_data')

        if dimension.table and data.get('table_source_data') is not None:
            table_options = data.get('table_source_data').get('tableOptions')
            for key, val in table_options.items():
                if val is None:
                    table_options[key] = '[None]'
            data['table_source_data']['tableOptions'] = table_options
            dimension.table_source_data = data.get('table_source_data')

        db.session.add(dimension)
        db.session.commit()

        if 'ethnicity_category' in data:
            # Remove current value
            categorisation_service.unlink_dimension_from_family(dimension, 'Ethnicity')
            if data['ethnicity_category'] != '':
                # Add new value
                category = categorisation_service.get_categorisation_by_id(data['ethnicity_category'])
                categorisation_service.link_categorisation_to_dimension(dimension,
                                                                        category,
                                                                        data['include_parents'],
                                                                        data['include_all'],
                                                                        data['include_unknown'])


dimension_service = DimensionService()

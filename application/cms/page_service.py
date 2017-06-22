import json

from datetime import date
from slugify import slugify

from application.cms.exceptions import (
    PageUnEditable,
    PageNotFoundException,
    PageExistsException,
    DimensionAlreadyExists,
    DimensionNotFoundException
)

from application.cms.models import (
    Page,
    Meta,
    Dimension,
    DbPage,
    publish_status
)

from application import db
from application.cms.utils import DateEncoder


class PageService:

    # TODO store can be removed altogether as db is now store
    def __init__(self):
        self.store = None

    def init_app(self, app):
        self.store = None

    def create_page(self, page_type, parent=None, data=None, user=None):
        # TODO: Check page_type is valid
        # TODO: Make default parent homepage
        title = data['title']
        guid = data.pop('guid')
        publication_date = data.pop('publication_date')

        db_page = DbPage(guid=guid, uri=slugify(title),
                         parent_guid=parent,
                         page_type=page_type,
                         page_json=json.dumps(data),
                         publication_date=publication_date)
        db.session.add(db_page)
        db.session.commit()

        # TODO check db for guid and uri, should be unique
        # try:
        #     self.get_page(guid)
        #     raise PageExistsException
        # except PageNotFoundException:
        #     self.store.put_page(page)
        return db_page

    def get_topics(self):
        pages = DbPage.query.filter_by(page_type='topic').all()
        return pages

    # TODO remove
    def get_subtopics(self, page):
        subtopic_guids = self.store.get_subtopics(page)
        subtopics = []
        for guid in subtopic_guids:
            st = self.store.get(guid)
            measure_guids = self.store.get_measures(st)
            measures = []
            for m_guid in measure_guids:
                m = self.store.get(m_guid)
                measures.append(m)
            subtopics.append({'subtopic': st, 'measures': measures})
        return subtopics

    # TODO remove
    def get_pages(self):
        return self.store.get_pages()

    # TODO add error handling for query
    def get_page(self, guid):
        try:
            # TODO catch db exception for the one() and return 404
            page = DbPage.query.filter_by(guid=guid).one()
            return page
        except FileNotFoundError:
            raise PageNotFoundException

    # TODO add error handling for db update
    def create_dimension(self, page, title, time_period, summary, suppression_rules, disclosure_control,
                         type_of_statistic, location, source, user):

        guid = slugify(title).replace('-', '_')

        try:
            self.get_dimension(page, guid)
            raise DimensionAlreadyExists
        except DimensionNotFoundException:
            dimension = Dimension(guid=guid, title=title, time_period=time_period, summary=summary,
                                  suppression_rules=suppression_rules, disclosure_control=disclosure_control,
                                  type_of_statistic=type_of_statistic, location=location, source=source)
        return dimension

    # TODO add error handling for db update
    def update_measure_dimension(self, measure_page, dimension, chart_json):
        if measure_page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')

        data = {'chart': chart_json['chartObject'], 'chart_source_data': chart_json['source']}

        dimension = page_service.update_dimension(dimension, data)
        # page_service.update_dimension_source_data('chart.json', measure_page, dimension, chart_json['source'])

        measure_page.update_dimension(dimension)

        page_service.save_page(measure_page)

    # TODO change to use db
    def delete_dimension(self, page, guid, user):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        dimension = self.get_dimension(page, guid)
        page.dimensions.remove(dimension)
        message = "User: {} updated page: {} by deleting dimension {}".format(user, page.guid, guid)
        self.store.put_page(page, message=message)
        return dimension

    # TODO add error handling for db update
    def update_dimension(self, measure_page, dimension, data):
        dimension.title = data['title'] if 'title' in data else dimension.title
        dimension.time_period = data['time_period'] if 'time_period' in data else dimension.time_period
        dimension.summary = data['summary'] if 'summary' in data else dimension.summary
        dimension.chart = data['chart'] if 'chart' in data else dimension.chart
        dimension.table = data['table'] if 'table' in data else dimension.table
        dimension.suppression_rules = data['suppression_rules']\
            if 'suppression_rules' in data else dimension.suppression_rules
        dimension.disclosure_control = data['disclosure_control']\
            if 'disclosure_control' in data else dimension.disclosure_control
        dimension.type_of_statistic = data['type_of_statistic']\
            if 'type_of_statistic' in data else dimension.type_of_statistic
        dimension.location = data['location'] if 'location' in data else dimension.location
        dimension.source = data['source'] if 'source' in data else dimension.source
        if dimension.chart:
            dimension.chart_source_data = data.get('chart_source_data')
        measure_page.update_dimension(dimension)
        db.session.add(measure_page)
        db.session.commit()

    def get_dimension(self, page, guid):
        filtered = [d for d in page.dimensions if d.guid == guid]
        if len(filtered) == 0:
            raise DimensionNotFoundException
        else:
            return filtered[0]

    def update_dimension(self, page, dimension, data, user, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            dimension = self.get_dimension(page, dimension.guid)
            dimension.title = data['title'] if 'title' in data else dimension.title
            dimension.time_period = data['time_period'] if 'time_period' in data else dimension.time_period
            dimension.summary = data['summary'] if 'summary' in data else dimension.summary
            dimension.chart = data['chart'] if 'chart' in data else dimension.chart
            dimension.table = data['table'] if 'table' in data else dimension.table
            dimension.suppression_rules = data['suppression_rules']\
                if 'suppression_rules' in data else dimension.suppression_rules
            dimension.disclosure_control = data['disclosure_control']\
                if 'disclosure_control' in data else dimension.disclosure_control
            dimension.type_of_statistic = data['type_of_statistic']\
                if 'type_of_statistic' in data else dimension.type_of_statistic
            dimension.location = data['location'] if 'location' in data else dimension.location
            dimension.source = data['source'] if 'source' in data else dimension.source

            message = "User {} updating page: {} by editing dimension {}".format(user, page.guid, dimension.guid)
            self.store.put_page(page, message=message)

    # TODO change to use db
    def update_dimension_source_data(self, file, page, guid, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            dimension = self.get_dimension(page, guid)
            message = "Updating page: {} by add source data for dimension {}".format(page.guid, guid)
            self.store.put_dimension_json_data(page, dimension, data, file, message)

    # TODO remove
    def reload_dimension_source_data(self, file, measure, dimension):
        try:
            source_data = self.store.get_dimension_json_data(measure, dimension, file)
            return source_data
        except(PageNotFoundException, DimensionNotFoundException, FileNotFoundError):
            return {}

    def delete_dimension_source_chart(self, page, guid):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            self.store.delete_dimension_source_data(page, guid, 'chart.json')

    def delete_dimension_source_table(self, page, guid):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            self.store.delete_dimension_source_data(page, guid, 'table.json')

    def delete_dimension_source_data(self, page, guid):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            self.store.delete_dimension_source_data(page, guid)

    # TODO db error handling
    def update_page(self, page, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            publication_date = data.pop('publication_date')
            page.page_json = json.dumps(data, cls=DateEncoder)
            page.publication_date = publication_date

            # then update sections, meta etc. at some point?
            if message is None:
                message = 'Update for page: {}'.format(page.title)

            # TODO Check whether this was the agreed route
            # if page.publish_status() == "REJECTED":
            #     page.meta.status = 'DRAFT'
            #     message = "Updating page state for page: {} from REJECTED to DRAFT".format(page.guid)

        db.session.add(page)
        db.session.commit()

    # TODO db error handling
    def next_state(self, slug):
        page = self.get_page(slug)
        message = page.next_state()
        db.session.add(page)
        db.session.commit()
        return page

    # TODO db error handling
    def save_page(self, page):
        db.session.add(page)
        db.session.commit()

    # TODO db error handling
    def reject_page(self, slug):
        page = self.get_page(slug)
        message = page.reject()
        db.session.add(page)
        db.session.commit()

    def reject_page(self, slug, message):
        page = self.get_page(slug)
        message += page.reject()
        self.store.put_meta(page, message)
        return page

    # TODO send data to s3 bucket
    def upload_data(self, page, file):
        self.store.put_source_data(page, file)

    # TODO delete from s3 bucker
    def delete_upload(self, page, file):
        self.store.delete_upload(page, file)

    def get_page_by_uri(self, subtopic, measure):
        page = DbPage.query.filter_by(uri=measure, parent_guid=subtopic).one()
        return page

    def mark_page_published(self, page):
        page.publication_date = date.today()
        page.meta.published = True
        message = 'Page %s published on %s' % (page.guid, page.publication_date.strftime('%Y-%m-%d'))
        self.store.put_page(page, message=message)


page_service = PageService()

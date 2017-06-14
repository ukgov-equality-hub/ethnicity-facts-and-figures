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

from application.cms.stores import GitStore
from application import db


class PageService:

    def __init__(self):
        self.store = None

    def init_app(self, app):
        self.store = GitStore(app.config)

    def create_page(self, page_type, parent=None, data=None):
        # TODO: Check page_type is valid
        # TODO: Make default parent homepage
        title = data['title']
        guid = data.pop('guid')

        meta = Meta(guid=guid, uri=slugify(title), parent=parent, page_type=page_type)
        page = Page(title, data, meta=meta)

        db_page = DbPage(guid=guid, uri=slugify(title),
                         parent_guid=parent,
                         page_type=page_type,
                         page_json=page.to_json())
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

    def get_pages(self):
        return self.store.get_pages()

    def get_page(self, guid):
        try:
            # TODO catch proper exception for the one() and return 404
            page = DbPage.query.filter_by(guid=guid).one()
            return page
        except FileNotFoundError:
            raise PageNotFoundException

    def create_dimension(self, page, title, time_period, summary, suppression_rules, disclosure_control,
                         type_of_statistic, location, source):

        guid = slugify(title).replace('-', '_')

        try:
            self.get_dimension(page, guid)
            raise DimensionAlreadyExists
        except DimensionNotFoundException:
            dimension = Dimension(guid=guid, title=title, time_period=time_period, summary=summary,
                                  suppression_rules=suppression_rules, disclosure_control=disclosure_control,
                                  type_of_statistic=type_of_statistic, location=location, source=source)
            page.dimensions.append(dimension)
            message = "Updating page: {} by creating dimension {}".format(page.guid, guid)
            self.store.put_page(page, message=message)
        return dimension

    def delete_dimension(self, page, guid):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        dimension = self.get_dimension(page, guid)
        page.dimensions.remove(dimension)
        message = "Updating page: {} by deleting dimension {}".format(page.guid, guid)
        self.store.put_page(page, message=message)
        return dimension

    def get_dimension(self, page, guid):
        filtered = [d for d in page.dimensions() if d['guid'] == guid]
        if len(filtered) == 0:
            raise DimensionNotFoundException
        else:
            d = filtered[0]
            return Dimension(**d)

    def update_dimension(self, page, dimension, data, message=None):
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

            message = "Updating page: {} by editing dimension {}".format(page.guid, dimension.guid)
            self.store.put_page(page, message=message)

    def update_dimension_source_data(self, file, page, guid, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            dimension = self.get_dimension(page, guid)
            message = "Updating page: {} by add source data for dimension {}".format(page.guid, guid)
            self.store.put_dimension_json_data(page, dimension, data, file, message)

    def reload_dimension_source_data(self, file, measure_guid, dimension_guid):
        try:
            page = self.get_page(measure_guid)
            dimension = self.get_dimension(page, dimension_guid)
            source_data = self.store.get_dimension_json_data(page, dimension, file)
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

    def update_page(self, page, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            page.title = data['title']
            for key, value in data.items():
                setattr(page, key, value)

            # then update sections, meta etc. at some point?
            if message is None:
                message = 'Update for page: {}'.format(page.title)
            self.store.put_page(page, message=message)

            # TODO Check whether this was the agreed route
            if page.publish_status() == "REJECTED":
                page.meta.status = 'DRAFT'
                message = "Updating page state for page: {} from REJECTED to DRAFT".format(page.guid)
                self.store.put_meta(page, message)

        db_page = DbPage.query.filter_by(guid=page.meta.guid).one()
        db_page.status = page.meta.status
        db.page_json = page.to_json()
        db.session.add(db_page)
        db.session.commit()

    def next_state(self, slug):
        page = self.get_page(slug)
        message = page.next_state()
        self.store.put_meta(page, message)
        return page

    def save_page(self, page):
        self.store.put_page(page)

    def reject_page(self, slug):
        page = self.get_page(slug)
        message = page.reject()
        self.store.put_meta(page, message)
        return page

    def upload_data(self, page, file):
        self.store.put_source_data(page, file)

    def delete_upload(self, page, file):
        self.store.delete_upload(page, file)

    def get_measure_guid(self, subtopic, measure):
        subtopic = self.get_page(subtopic)
        measures = self.store.get_measures(subtopic)
        for m in measures:
            m_page = self.get_page(m)
            if m_page.meta.uri == measure:
                return m
        return None


page_service = PageService()

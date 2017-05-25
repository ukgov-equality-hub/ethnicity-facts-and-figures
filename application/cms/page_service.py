from slugify import slugify

from application.cms.exceptions import (
    PageUnEditable,
    PageNotFoundException,
    DimensionAlreadyExists,
    DimensionNotFoundException
)

from application.cms.models import (
    Page,
    Meta,
    Dimension)

from application.cms.stores import GitStore


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
        self.store.put_page(page)
        return page

    def get_pages(self):
        return self.store.list()

    def get_page(self, guid):
        try:
            return self.store.get(guid)
        except FileNotFoundError:
            raise PageNotFoundException

    def create_dimension(self, page, title, time_period, summary):
        print(title, type(title))
        guid = slugify(title).replace('-', '_')

        try:
            self.get_dimension(page, guid)
            raise DimensionAlreadyExists
        except DimensionNotFoundException:
            dimension = Dimension(guid=guid, title=title, time_period=time_period, summary=summary)
            page.dimensions.append(dimension)
            message = "Updating page: {} by creating dimension {}".format(page.guid, guid)
            self.store.put_page(page, message=message)
        return dimension

    def get_dimension(self, page, guid):
        filtered = [d for d in page.dimensions if d.guid == guid]
        if len(filtered) == 0:
            raise DimensionNotFoundException
        else:
            return filtered[0]

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

    def get_measure_guid(self, subtopic, measure):
        subtopic = self.get_page(subtopic)
        for m in subtopic.subtopics:
            m_page = self.get_page(m)
            if m_page.meta.uri == measure:
                return m
        return None


page_service = PageService()

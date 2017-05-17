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

    def create_dimension(self, page, title, description=''):
        guid = slugify(title).replace('-', '_')

        try:
            self.get_dimension(page, guid)
            raise DimensionAlreadyExists
        except DimensionNotFoundException:
            page.dimensions.append(Dimension(guid=guid, title=title, description=description))
            message = "Updating page: {} by creating dimension {}".format(page.guid, guid)
            self.store.put_page(page, message=message)

    def get_dimension(self, page, guid):
        filtered = [d for d in page.dimensions if d.guid == guid]
        if len(filtered) == 0:
            raise DimensionNotFoundException
        else:
            return filtered[0]

    def update_dimension(self, page, guid, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            dimension = self.get_dimension(page, guid)
            dimension.title = data['title'] if 'title' in data else dimension.title
            dimension.description = data['description'] if 'description' in data else dimension.description
            dimension.chart = data['chart'] if 'chart' in data else dimension.chart
            dimension.table = data['table'] if 'table' in data else dimension.table

            message = "Updating page: {} by editing dimension {}".format(page.guid, guid)
            self.store.put_page(page, message=message)

    def update_chart_source_data(self, page, guid, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            dimension = self.get_dimension(page, guid)
            message = "Updating page: {} by add chart data for dimension {}".format(page.guid, guid)
            self.store.put_dimension_json_data(page, dimension, data, 'chart.json', message)

    def reload_chart(self, measure_guid, dimension_guid):
        try:
            page = self.get_page(measure_guid)
            dimension = self.get_dimension(page, dimension_guid)
            chart_data = self.store.get_dimension_json_data(page, dimension, 'chart.json')
            return chart_data
        except(PageNotFoundException, DimensionNotFoundException):
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

            if page.publish_status() == "REJECTED":
                page.meta.status = 'INTERNAL_REVIEW'
                message = "Updating page state for page: {} from REJECTED to INTERNAL_REVIEW".format(page.guid)
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


page_service = PageService()

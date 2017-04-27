from slugify import slugify

from application.cms.exceptions import (
    PageUnEditable,
    PageNotFoundException
)

from application.cms.models import (
    Page,
    Meta
)

from application.cms.stores import GitStore


class PageService:

    def __init__(self):
        self.store = None

    def init_app(self, app):
        self.store = GitStore(app.config)

    def create_page(self, data=None):
        title = data['title']
        meta = Meta(uri=slugify(title), parent=None, page_type='topic')
        page = Page(title=data['title'], description=None, meta=meta, content=None)
        self.store.put_page(page)
        return page

    def get_pages(self):
        return self.store.list()

    def get_page(self, slug):
        guid = 'topic_%s' % slug.replace('-', '')
        try:
            return self.store.get(guid)
        except FileNotFoundError:
            raise PageNotFoundException

    def update_page(self, page, data, message=None):
        if page.not_editable():
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            page.title = data['title']
            page.description = data['description']
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

    def reject_page(self, slug):
        page = self.get_page(slug)
        message = page.reject()
        self.store.put_meta(page, message)
        return page


page_service = PageService()

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import PageNotFoundException
from application.cms.models import MeasureVersion
from application.cms.service import Service


class PageService(Service):
    def __init__(self):
        super().__init__()

    def get_page(self, guid):  # TODO: Kill this with fire.
        try:
            return MeasureVersion.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_page_with_title(self, title):
        try:
            return MeasureVersion.query.filter_by(title=title).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    @staticmethod
    def get_pages_by_type(page_type):
        return (
            MeasureVersion.query.filter_by(page_type=page_type)
            .order_by(MeasureVersion.title, desc(MeasureVersion.version))
            .all()
        )


page_service = PageService()

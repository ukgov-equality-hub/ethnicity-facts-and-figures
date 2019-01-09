from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import PageNotFoundException
from application.cms.models import Topic, MeasureVersion
from application.cms.service import Service


class NewPageService(Service):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_topic(slug):
        try:
            return Topic.query.filter_by(slug=slug).one()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_measure_by_id(measure_id):
        try:
            # TODO: Use `query.get` instead of `query.filter_by` after removing guid+version from MeasureVersion PK
            return MeasureVersion.query.filter_by(id=measure_id).one().measure
        except NoResultFound:
            raise PageNotFoundException()


new_page_service = NewPageService()

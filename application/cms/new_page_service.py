from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import PageNotFoundException
from application.cms.models import Topic
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


new_page_service = NewPageService()

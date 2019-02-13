from sqlalchemy import desc

from application.cms.models import MeasureVersion
from application.cms.service import Service


class PageService(Service):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_pages_by_type(page_type):  # TODO: Kill this too when fixing dashboards
        return (
            MeasureVersion.query.filter_by(page_type=page_type)
            .order_by(MeasureVersion.title, desc(MeasureVersion.version))
            .all()
        )


page_service = PageService()

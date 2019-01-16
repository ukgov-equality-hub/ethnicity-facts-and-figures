from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from application import db
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

    @staticmethod
    def get_latest_publishable_measures(subtopic):
        filtered = []
        seen = set([])
        for m in subtopic.children:
            if m.guid not in seen:
                versions = m.get_versions()
                versions.sort(reverse=True)
                for v in versions:
                    if v.eligible_for_build():
                        filtered.append(v)
                        seen.add(v.guid)
                        break
        return filtered

    @staticmethod
    def get_previous_major_versions(measure):
        versions = measure.get_versions(include_self=False)
        versions.sort(reverse=True)
        versions = [v for v in versions if v.major() < measure.major() and not v.has_minor_update()]
        return versions

    @staticmethod
    def get_previous_minor_versions(measure):
        versions = measure.get_versions(include_self=False)
        versions.sort(reverse=True)
        versions = [v for v in versions if v.major() == measure.major() and v.minor() < measure.minor()]
        return versions

    @staticmethod
    def get_first_published_date(measure):
        versions = page_service.get_previous_minor_versions(measure)
        return versions[-1].published_at if versions else measure.published_at

    @staticmethod
    def get_pages_to_unpublish():
        return (
            MeasureVersion.query.filter_by(status="UNPUBLISH")
            .order_by(MeasureVersion.title, desc(MeasureVersion.version))
            .all()
        )

    @staticmethod
    def mark_pages_unpublished(pages):
        for page in pages:
            page.published = False
            page.published_at = None  # TODO: Don't unset this (need to update logic around whether published or not)
            page.unpublished_at = datetime.datetime.now()
            page.status = "UNPUBLISHED"
            db.session.commit()


page_service = PageService()

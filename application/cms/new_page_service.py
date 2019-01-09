from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import (
    PageNotFoundException,
    InvalidPageHierarchy,
    UploadNotFoundException,
    DimensionNotFoundException,
)
from application.cms.models import Measure, MeasureVersion, Subtopic, Topic
from application.cms.service import Service


class NewPageService(Service):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_topic(topic_slug):
        try:
            return Topic.query.filter_by(slug=topic_slug).one()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_subtopic(topic_slug, subtopic_slug):
        try:
            return Subtopic.query.filter(
                Subtopic.topic.has(Topic.slug == topic_slug), Subtopic.slug == subtopic_slug
            ).one()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_measure(topic_slug, subtopic_slug, measure_slug):
        try:
            measures_with_matching_slug = Measure.query.filter(Measure.slug == measure_slug).all()
            for measure in measures_with_matching_slug:
                if measure.subtopic.topic.slug == topic_slug and measure.subtopic.slug == subtopic_slug:
                    return measure
            raise PageNotFoundException()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_measure_version(topic_slug, subtopic_slug, measure_slug, version):
        try:
            measure_versions_with_matching_slug_and_version = MeasureVersion.query.filter(
                MeasureVersion.measure.has(Measure.slug == measure_slug), MeasureVersion.version == version
            ).all()
            for measure_version in measure_versions_with_matching_slug_and_version:
                if (
                    measure_version.measure.subtopic.topic.slug == topic_slug
                    and measure_version.measure.subtopic.slug == subtopic_slug
                ):
                    return measure_version
            raise PageNotFoundException()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_measure_from_measure_version_id(measure_version_id):
        try:
            # TODO: Use `query.get` instead of `query.filter_by` after removing guid+version from MeasureVersion PK
            return MeasureVersion.query.filter_by(id=measure_version_id).one().measure
        except NoResultFound:
            raise PageNotFoundException()

    def get_measure_page_hierarchy(
        self, topic_slug, subtopic_slug, measure_slug, version, dimension_guid=None, upload_guid=None
    ):
        try:
            topic = new_page_service.get_topic(topic_slug)
            subtopic = new_page_service.get_subtopic(topic_slug, subtopic_slug)
            measure = new_page_service.get_measure(topic_slug, subtopic_slug, measure_slug)
            measure_version = new_page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)
            dimension_object = measure_version.get_dimension(dimension_guid) if dimension_guid else None
            upload_object = measure_version.get_upload(upload_guid) if upload_guid else None
        except PageNotFoundException:
            self.logger.exception("Page id: {} not found".format(measure_slug))
            raise InvalidPageHierarchy
        except UploadNotFoundException:
            self.logger.exception("Upload id: {} not found".format(upload_guid))
            raise InvalidPageHierarchy
        except DimensionNotFoundException:
            self.logger.exception("Dimension id: {} not found".format(dimension_guid))
            raise InvalidPageHierarchy

        return_items = [topic, subtopic, measure, measure_version]
        if dimension_object:
            return_items.append(dimension_object)
        if upload_object:
            return_items.append(upload_object)

        return (item for item in return_items)


new_page_service = NewPageService()

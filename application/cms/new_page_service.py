import uuid

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func

from application import db
from application.cms.models import publish_status, DataSource
from application.cms.exceptions import (
    PageNotFoundException,
    InvalidPageHierarchy,
    UploadNotFoundException,
    DimensionNotFoundException,
    PageExistsException,
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
            measure = Measure.query.filter(
                Measure.subtopics.any(Subtopic.topic.has(Topic.slug == topic_slug)),
                Measure.subtopics.any(Subtopic.slug == subtopic_slug),
                Measure.slug == measure_slug,
            ).one()
            return measure
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
            self.logger.exception("Page slug: {} not found".format(measure_slug))
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

    @staticmethod
    def get_previous_major_versions(measure_version):
        versions = measure_version.get_versions(include_self=False)
        versions.sort(reverse=True)
        versions = [v for v in versions if v.major() < measure_version.major() and not v.has_minor_update()]
        return versions

    @staticmethod
    def get_previous_minor_versions(measure_version):
        versions = measure_version.get_versions(include_self=False)
        versions.sort(reverse=True)
        versions = [v for v in versions if v.major() == measure_version.major() and v.minor() < measure_version.minor()]
        return versions

    def get_first_published_date(self, measure_version):
        versions = self.get_previous_minor_versions(measure_version)
        return versions[-1].published_at if versions else measure_version.published_at

    @staticmethod
    def get_latest_version_of_all_measures(include_drafts=False):
        measure_query = MeasureVersion.query

        cte = (
            MeasureVersion.query.with_entities(
                MeasureVersion.measure_id, func.max(MeasureVersion.version).label("max_version")
            )
            .filter(MeasureVersion.published == (not include_drafts))
            .group_by(MeasureVersion.measure_id)
            .cte("max_measure_version")
        )

        measure_query = measure_query.filter(
            MeasureVersion.measure_id == cte.c.measure_id, MeasureVersion.version == cte.c.max_version
        )

        return measure_query.order_by(MeasureVersion.title).all()

    def _set_data_sources(self, page, data_source_forms):
        current_data_sources = page.data_sources
        page.data_sources = []

        for i, data_source_form in enumerate(data_source_forms):
            existing_source = len(current_data_sources) > i

            if data_source_form.remove_data_source.data or not any(
                value for key, value in data_source_form.data.items() if key != "csrf_token"
            ):
                if existing_source:
                    db.session.delete(current_data_sources[i])

            else:
                data_source = current_data_sources[i] if existing_source else DataSource()
                data_source_form.populate_obj(data_source)

                source_has_truthy_values = any(
                    getattr(getattr(data_source_form, column.name), "data")
                    for column in DataSource.__table__.columns
                    if column.name != "id"
                )

                if existing_source or source_has_truthy_values:
                    page.data_sources.append(data_source)

    def create_measure(self, subtopic, measure_page_form, data_source_forms, created_by_email):
        title = measure_page_form.data.pop("title", "").strip()
        guid = str(uuid.uuid4())
        slug = slugify(title)

        if Measure.query.filter(Measure.slug == slug, Measure.subtopics.contains(subtopic)).all():
            raise PageExistsException(
                f'Measure with title "{title}" already exists under the "{subtopic.title}" subtopic.'
            )

        measure = Measure(
            slug=slug, position=len(subtopic.measures), reference=measure_page_form.data.get("internal_reference", None)
        )
        measure.subtopics = [subtopic]
        db.session.add(measure)
        db.session.flush()

        # TODO: Remove me. A bit of a hack to tie a measure version up to a subtopic measure version, so that `.parent`
        # references resolve. This eases the development process.
        subtopic_page = MeasureVersion.query.filter(
            MeasureVersion.page_type == "subtopic", MeasureVersion.slug == subtopic.slug
        ).one()

        measure_version = MeasureVersion(
            guid=guid,
            version="1.0",
            slug=slug,
            title=title,
            measure_id=measure.id,
            status=publish_status.inv[1],
            created_by=created_by_email,
            position=len(subtopic.measures),
            parent_id=subtopic_page.id,
            parent_guid=subtopic_page.guid,
            parent_version=subtopic_page.version,
        )

        measure_page_form.populate_obj(measure_version)

        self._set_data_sources(page=measure_version, data_source_forms=data_source_forms)

        db.session.add(measure_version)
        db.session.commit()

        previous_version = measure_version.get_previous_version()
        if previous_version is not None:
            previous_version.latest = False
            db.session.commit()

        return measure_version


new_page_service = NewPageService()

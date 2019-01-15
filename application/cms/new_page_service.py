import uuid
from datetime import datetime

from slugify import slugify
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import (
    DimensionNotFoundException,
    InvalidPageHierarchy,
    PageExistsException,
    PageNotFoundException,
    UpdateAlreadyExists,
    UploadNotFoundException,
    PageUnEditable,
    StaleUpdateException,
    CannotChangeSubtopicOncePublished,
)
from application.cms.models import DataSource, Measure, MeasureVersion, Subtopic, Topic, publish_status, NewVersionType
from application.cms.service import Service
from application.cms.upload_service import upload_service
from application.utils import create_guid


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
    def get_all_topics():
        return sorted(Topic.query.filter(Topic.slug != "testing-space").all(), key=lambda topic: topic.title)

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
    def get_measure_version_by_id(measure_id, version):
        return MeasureVersion.query.filter(
            MeasureVersion.measure.has(Measure.id == measure_id), MeasureVersion.version == version
        ).one_or_none()

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

    @staticmethod
    def _is_stale_update(data, page):
        update_db_version_id = int(data.pop("db_version_id"))
        if update_db_version_id < page.db_version_id:
            return new_page_service._page_and_data_have_diffs(data, page)
        else:
            return False

    @staticmethod
    def _page_and_data_have_diffs(data, page):
        for key, update_value in data.items():
            if hasattr(page, key) and key != "db_version_id":
                existing_page_value = getattr(page, key)
                if update_value != existing_page_value:
                    if type(existing_page_value) == type(str) and existing_page_value.strip() == "":
                        # The existing_page_value is empty so we don't count it as a conflict
                        return False
                    else:
                        # The existing_page_value isn't empty and differs from the submitted value in data
                        return True
        return False

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

    def create_measure_version(self, measure_version, update_type, user):
        next_version_number = measure_version.next_version_number_by_type(update_type)

        if update_type != NewVersionType.NEW_MEASURE and self.get_measure_version_by_id(
            measure_version.measure_id, next_version_number
        ):
            raise UpdateAlreadyExists()

        new_version = measure_version.copy()
        new_version.guid = measure_version.guid

        if update_type == NewVersionType.NEW_MEASURE:
            new_version.guid = str(uuid.uuid4())
            new_version.title = f"COPY OF {measure_version.title}"

            # TODO: Remove this later when we stop duplicating to the MeasureVersion table.
            try:
                while self.get_measure(
                    measure_version.measure.subtopic.topic.slug, measure_version.measure.subtopic.slug, new_version.slug
                ):
                    new_version.slug = f"{new_version.slug}-copy"

            except PageNotFoundException:
                pass

            new_version.measure = Measure(
                slug=new_version.slug,
                position=len(measure_version.measure.subtopic.measures),
                reference=measure_version.internal_reference,
            )
            new_version.measure.subtopics = measure_version.measure.subtopics

        new_version.version = next_version_number
        new_version.status = "DRAFT"
        new_version.created_by = user.email
        new_version.created_at = datetime.utcnow()
        new_version.published_at = None
        new_version.published = False
        new_version.internal_edit_summary = None
        new_version.external_edit_summary = None
        new_version.dimensions = [dimension.copy() for dimension in measure_version.dimensions]
        new_version.data_sources = [data_source.copy() for data_source in measure_version.data_sources]
        new_version.latest = True

        previous_version = new_version.get_previous_version()
        if previous_version:
            previous_version.latest = False
            db.session.add(previous_version)

        new_version.uploads = []
        for upload in measure_version.uploads:
            new_upload = upload.copy()
            new_upload.guid = create_guid(upload.file_name)
            new_version.uploads.append(new_upload)

        db.session.add(new_version)
        db.session.flush()

        upload_service.copy_uploads_between_measure_versions(
            from_measure_version=measure_version, to_measure_version=new_version
        )

        db.session.commit()

        return new_version

    def update_measure_version(  # noqa: C901 (complexity)
        self, measure_version, measure_page_form, data_source_forms, last_updated_by_email, **kwargs
    ):
        if measure_version.not_editable():
            message = "Error updating '{}': Versions not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(
                measure_version.title
            )
            self.logger.error(message)
            raise PageUnEditable(message)
        elif new_page_service._is_stale_update(measure_page_form.data, measure_version):
            raise StaleUpdateException("")

        # Possibly temporary to work out issue with data deletions
        message = "EDIT MEASURE: Current state of measure_version: %s" % measure_version.to_dict()
        self.logger.info(message)
        message = "EDIT MEASURE: Data posted to update measure_version: %s" % measure_page_form.data
        self.logger.info(message)

        subtopic_id_from_form = kwargs.get("subtopic_id")
        if subtopic_id_from_form is not None and measure_version.measure.subtopic.id != int(subtopic_id_from_form):
            if measure_version.version != "1.0":
                raise CannotChangeSubtopicOncePublished
            new_subtopic = Subtopic.query.get(subtopic_id_from_form)

            conflicting_url = [msure for msure in new_subtopic.measures if msure.slug == measure_version.measure.slug]
            if conflicting_url:
                message = f"A measure with url '{measure_version.slug}' already exists in {new_subtopic.title}"
                raise PageExistsException(message)
            else:
                measure_version.measure.subtopics = [new_subtopic]
                measure_version.measure.position = len(new_subtopic.measures)

                # TODO: Remove this once we drop the parent relationship and remove subtopic/topics from MeasureVersion
                subtopic_pages_matching_slug = MeasureVersion.query.filter_by(
                    page_type="subtopic", slug=new_subtopic.slug
                ).all()
                # This will raise StopIteration if no subtopic page is found with a matching topic
                new_subtopic_page = next(
                    filter(lambda st: st.parent.slug == new_subtopic.topic.slug, subtopic_pages_matching_slug)
                )
                measure_version.parent = new_subtopic_page
                measure_version.position = len(new_subtopic_page.children)
                # TODO: End of code to remove

        status = kwargs.get("status")
        if status is not None:
            measure_version.status = status

        measure_page_form.data.pop("guid", None)  # TODO: Remove this?
        title = measure_page_form.data.pop("title").strip()
        measure_version.title = title
        if measure_version.version == "1.0":
            slug = slugify(title)

            if slug != measure_version.slug and self._new_slug_invalid(measure_version, slug):
                message = (
                    f"A page '{title}' with slug '{slug}' already exists under {measure_version.measure.subtopic.title}"
                )
                raise PageExistsException(message)
            measure_version.measure.slug = slug
            measure_version.slug = slug  # TODO: Remove this once slug is gone from MeasureVersion

        # Update main fields of MeasureVersion
        measure_page_form.populate_obj(measure_version)
        self._set_data_sources(page=measure_version, data_source_forms=data_source_forms)

        # Update fields in the parent Measure
        if "internal_reference" in measure_page_form.data:
            reference = measure_page_form.data["internal_reference"]
            measure_version.measure.reference = reference if reference else None

        if measure_version.publish_status() in ["REJECTED", "UNPUBLISHED"]:
            new_status = publish_status.inv[1]
            measure_version.status = new_status

        measure_version.updated_at = datetime.utcnow()
        measure_version.last_updated_by = last_updated_by_email

        db.session.commit()

        return measure_version

    @staticmethod
    def _new_slug_invalid(measure_version, new_slug):
        if MeasureVersion.query.filter(
            Topic.slug == measure_version.measure.subtopic.topic.slug,
            Subtopic.slug == measure_version.measure.subtopic.slug,
            Measure.slug == new_slug,
        ).first():
            return True
        else:
            return False

    def reject_measure_version(self, measure_version: MeasureVersion):
        message = measure_version.reject()
        db.session.commit()
        self.logger.info(message)
        return message

    def unpublish_measure_version(self, measure_version: MeasureVersion, unpublished_by: str):
        message = measure_version.unpublish()
        measure_version.unpublished_by = unpublished_by
        db.session.commit()
        self.logger.info(message)
        return message

    def send_measure_version_to_draft(self, measure_version: MeasureVersion):
        available_actions = measure_version.available_actions()

        if "RETURN_TO_DRAFT" in available_actions:
            numerical_status = measure_version.publish_status(numerical=True)
            measure_version.status = publish_status.inv[(numerical_status + 1) % 6]
            db.session.commit()
            message = 'Sent measure_version "{}" back to {}'.format(measure_version.title, measure_version.status)
        else:
            message = 'Page "{}" can not be updated'.format(measure_version.title)

        return message

    def delete_measure_version(self, measure_version: MeasureVersion):
        previous_version = measure_version.get_previous_version()
        if previous_version:
            previous_version.latest = True
        else:
            #  We're deleting a a 1.0 version and so need to also delete the associated Measure
            db.session.delete(measure_version.measure)
        db.session.delete(measure_version)
        db.session.commit()


new_page_service = NewPageService()

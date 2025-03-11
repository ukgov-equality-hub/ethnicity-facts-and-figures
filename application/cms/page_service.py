from datetime import datetime, date
from typing import Iterable, Tuple, List

from flask import request
from slugify import slugify
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
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
from application.cms.models import (
    Measure,
    MeasureVersion,
    Subtopic,
    Topic,
    publish_status,
    NewVersionType,
    TESTING_SPACE_SLUG,
)
from application.cms.service import Service
from application.cms.upload_service import upload_service
from application.sitebuilder.build_service import request_build
from application.utils import create_guid, generate_review_token
from flask import current_app
import boto3
import boto3.session
import botocore


class PageService(Service):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_topic(topic_slug):
        try:
            return Topic.query.filter_by(slug=topic_slug).one()
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_topic_with_subtopics_and_measures(topic_slug):
        """Returns a Topic, the same as `get_topic`, but pre-loads the subtopics and measures in order to avoid
        subsequent queries going back and forth to the database."""
        try:
            return (
                Topic.query.options(
                    joinedload(Topic.subtopics).joinedload(Subtopic.measures).joinedload(Measure.versions)
                )
                .filter(Topic.slug == topic_slug)
                .one()
            )
        except NoResultFound:
            raise PageNotFoundException()

    @staticmethod
    def get_topics(include_testing_space):
        topic_query = Topic.query

        if not include_testing_space:
            topic_query = topic_query.filter(Topic.slug != TESTING_SPACE_SLUG)

        return sorted(topic_query.all(), key=lambda topic: topic.title)

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
    def get_measure_version_by_measure_id_and_version(measure_id, version):
        return MeasureVersion.query.filter(
            MeasureVersion.measure.has(Measure.id == measure_id), MeasureVersion.version == version
        ).one_or_none()

    @staticmethod
    def get_measure_from_measure_version_id(measure_version_id):
        measure_version = MeasureVersion.query.get(measure_version_id)
        if measure_version:
            return measure_version.measure
        else:
            raise PageNotFoundException()

    @staticmethod
    def get_measure_version_by_id(measure_version_id):
        measure_version = MeasureVersion.query.get(measure_version_id)
        if measure_version:
            return measure_version
        else:
            raise PageNotFoundException()

    def get_measure_version_hierarchy(
        self, topic_slug, subtopic_slug, measure_slug, version, dimension_guid=None, upload_guid=None
    ):
        try:
            topic = page_service.get_topic(topic_slug)
            subtopic = page_service.get_subtopic(topic_slug, subtopic_slug)
            measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)
            measure_version = page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)
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
    def get_latest_version_of_all_measures(include_not_published=True):
        cte = MeasureVersion.query.with_entities(
            MeasureVersion.measure_id, func.max(MeasureVersion.version).label("max_version")
        )
        if not include_not_published:
            cte = cte.filter(MeasureVersion.status == "APPROVED")
        cte = cte.group_by(MeasureVersion.measure_id).cte("max_measure_version")

        measure_query = MeasureVersion.query.filter(
            MeasureVersion.measure_id == cte.c.measure_id, MeasureVersion.version == cte.c.max_version
        )

        return measure_query.order_by(MeasureVersion.title).all()

    @staticmethod
    def _is_stale_update(data, page):
        update_db_version_id = int(data.pop("db_version_id"))
        if update_db_version_id < page.db_version_id:
            return page_service._page_and_data_have_diffs(data, page)
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

    def create_measure(self, subtopic, measure_version_form, created_by_email):
        title = measure_version_form.data.pop("title", "").strip()
        slug = slugify(title)

        if Measure.query.filter(Measure.slug == slug, Measure.subtopics.contains(subtopic)).all():
            raise PageExistsException(
                f'Measure with title "{title}" already exists under the "{subtopic.title}" subtopic.'
            )

        measure = Measure(
            slug=slug,
            position=len(subtopic.measures),
            reference=measure_version_form.data.get("internal_reference", None),
        )
        measure.subtopics = [subtopic]
        db.session.add(measure)
        db.session.flush()

        measure_version = MeasureVersion(
            version="1.0", title=title, measure_id=measure.id, status=publish_status.inv[1], created_by=created_by_email
        )

        measure_version_form.populate_obj(measure_version)

        db.session.add(measure_version)
        db.session.commit()

        previous_version = measure_version.get_previous_version()
        if previous_version is not None:
            previous_version.latest = False
            db.session.commit()

        return measure_version

    def create_measure_version(self, measure_version, update_type, user, created_by_api=False):
        next_version_number = measure_version.next_version_number_by_type(update_type)

        if update_type != NewVersionType.NEW_MEASURE and self.get_measure_version_by_measure_id_and_version(
            measure_version.measure_id, next_version_number
        ):
            raise UpdateAlreadyExists()

        new_version = measure_version.copy(exclude_fields=["update_corrects_data_mistake"])

        if update_type == NewVersionType.NEW_MEASURE:
            new_version.title = f"COPY OF {measure_version.title}"

            new_slug = f"{measure_version.measure.slug}-copy"
            # In case there are multiple -copy measures, try this...
            try:
                while self.get_measure(
                    measure_version.measure.subtopic.topic.slug, measure_version.measure.subtopic.slug, new_slug
                ):
                    new_slug = f"{new_slug}-copy"
            except PageNotFoundException:
                pass

            new_version.measure = Measure(slug=new_slug, position=len(measure_version.measure.subtopic.measures))
            new_version.measure.subtopics = measure_version.measure.subtopics
        else:
            # We insert to the front of the `measure.versions` relationship so that we maintain ordering of
            # desc(measure_version.version) as defined by the relationship on the model, as otherwise the list is not
            # updated by sqlalchemy until a commit.
            new_version.version = next_version_number
            measure_version.measure.versions.insert(0, new_version)

        new_version.version = next_version_number
        new_version.status = "DRAFT"
        new_version.created_by = "API" if created_by_api else user.email
        new_version.created_at = datetime.utcnow()
        new_version.published_at = None
        new_version.internal_edit_summary = None
        new_version.external_edit_summary = None
        new_version.uploads = []
        new_version.dimensions = [dimension.copy() for dimension in measure_version.dimensions]
        new_version.latest = True

        # We don't copy uploads or data sources for major updates, as major updates should always have new data
        if update_type != NewVersionType.MAJOR_UPDATE:
            for upload in measure_version.uploads:
                new_upload = upload.copy()
                new_upload.guid = create_guid(upload.file_name)
                new_version.uploads.append(new_upload)

            new_version.data_sources = measure_version.data_sources

        db.session.add(new_version)
        db.session.flush()

        upload_service.copy_uploads_between_measure_versions(
            from_measure_version=measure_version, to_measure_version=new_version
        )

        previous_version = new_version.get_previous_version()
        if previous_version:
            previous_version.latest = False
            db.session.add(previous_version)

        db.session.commit()

        return new_version

    def update_measure_version(  # noqa: C901 (complexity)
        self, measure_version, measure_version_form, last_updated_by_email, **kwargs
    ):
        if measure_version.not_editable():
            message = "Error updating '{}': Versions not in DRAFT, REJECT can't be edited".format(measure_version.title)
            self.logger.error(message)
            raise PageUnEditable(message)
        elif page_service._is_stale_update(measure_version_form.data, measure_version):
            raise StaleUpdateException("")

        # Possibly temporary to work out issue with data deletions
        message = "EDIT MEASURE: Current state of measure_version: %s" % measure_version.to_dict()
        self.logger.info(message)
        message = "EDIT MEASURE: Request data: %s" % request.form
        self.logger.info(message)
        message = "EDIT MEASURE: WTForm data to update measure version: %s" % measure_version_form.data
        self.logger.info(message)

        subtopic_id_from_form = kwargs.get("subtopic_id")
        if subtopic_id_from_form is not None and measure_version.measure.subtopic.id != int(subtopic_id_from_form):
            if measure_version.version != "1.0":
                raise CannotChangeSubtopicOncePublished
            new_subtopic = Subtopic.query.get(subtopic_id_from_form)

            conflicting_url = [msure for msure in new_subtopic.measures if msure.slug == measure_version.measure.slug]
            if conflicting_url:
                message = f"A measure with url '{measure_version.measure.slug}' already exists in {new_subtopic.title}"
                raise PageExistsException(message)
            else:
                measure_version.measure.subtopics = [new_subtopic]
                measure_version.measure.position = len(new_subtopic.measures)

        status = kwargs.get("status")
        if status is not None:
            measure_version.status = status

        if measure_version.version == "1.0":
            slug = slugify(measure_version_form.title.data)

            if slug != measure_version.measure.slug and self._new_slug_invalid(measure_version, slug):
                message = f"A page with slug '{slug}' already exists under {measure_version.measure.subtopic.title}"
                raise PageExistsException(message)
            measure_version.measure.slug = slug

        # Update main fields of MeasureVersion
        measure_version_form.populate_obj(measure_version)

        # Update fields in the parent Measure
        if "internal_reference" in measure_version_form.data:
            reference = measure_version_form.data["internal_reference"]
            measure_version.measure.reference = reference if reference else None

        if measure_version.publish_status() == "REJECTED":
            measure_version.status = "DRAFT"

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

    def send_measure_version_to_draft(self, measure_version: MeasureVersion):
        if "RETURN_TO_DRAFT" in measure_version.available_actions:
            measure_version.status = "DRAFT"
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

    def archive_measure(self, measure: Measure, replaced_by_measure_id: int = None):
        measure.retired = True
        measure.replaced_by_measure_id = replaced_by_measure_id
        db.session.commit()

    def restore_measure(self, measure: Measure):
        measure.retired = False
        measure.replaced_by_measure_id = None
        db.session.commit()

    def mark_measure_version_published(self, measure_version: MeasureVersion):
        if measure_version.published_at is None:
            measure_version.published_at = date.today()

        measure_version.latest = True
        message = 'measure_version "{}" published on "{}"'.format(
            measure_version.id, measure_version.published_at.strftime("%Y-%m-%d")
        )
        self.logger.info(message)

        previous_version = measure_version.get_previous_version()
        if previous_version and previous_version.latest:
            previous_version.latest = False

        db.session.commit()

    @staticmethod
    def move_measure_version_to_next_state(measure_version: MeasureVersion, updated_by: str):
        message = measure_version.next_state()
        measure_version.last_updated_by = updated_by
        if measure_version.status == "DEPARTMENT_REVIEW":
            measure_version.review_token = generate_review_token(measure_version.id)
        if measure_version.status == "APPROVED":
            measure_version.published_by = updated_by
        db.session.commit()
        return message

    def update_measure_position_within_subtopic(self, *new_measure_positions: Iterable[Tuple[int, int, int]]):
        for new_measure_position in new_measure_positions:
            measure_id, subtopic_id, position = new_measure_position

            measure_version = MeasureVersion.query.filter(
                MeasureVersion.measure_id == measure_id,
                MeasureVersion.measure.has(Measure.subtopics.any(Subtopic.id == subtopic_id)),
            ).all()

            if measure_version:
                measure = Measure.query.get(measure_version[0].measure_id)
                measure.position = position

        db.session.commit()
        request_build()

    #  Methods below are used only by the static site build
    @staticmethod
    def get_publishable_measures_for_subtopic(subtopic):
        measures_to_publish = []
        for measure in subtopic.measures:
            if any(version.eligible_for_build() for version in measure.versions):
                measures_to_publish.append(measure)
        return measures_to_publish

    @staticmethod
    def first_published_date(measure_version):
        versions = measure_version.previous_minor_versions()
        return versions[-1].published_at if versions else measure_version.published_at

    @staticmethod
    def get_measure_versions_with_data_corrections() -> List[MeasureVersion]:

        return (
            MeasureVersion.query.filter(
                MeasureVersion.update_corrects_data_mistake == True,
                MeasureVersion.status == "APPROVED",
                MeasureVersion.published_at != None,
            )
            .order_by(desc(MeasureVersion.published_at))
            .all()
        )

    @staticmethod
    def valid_topic_title(title):
        if all(x.isalpha() or x.isspace() for x in title):
            return True
        return False

    @staticmethod
    def generate_topic_slug(title):
        return title.strip().lower().replace(" ", "-")

    @staticmethod
    def set_static_page_redirect(old_path, new_path):
        """Setting static page redirects when naming changes take place.

        This method is mainly used for setting up redirects automatically
        without a dev needed to go and set up them inside AWS. Correct page
        content eg breadcrumbs, will be updated with the build static script.
        """

        s3 = boto3.resource("s3")
        bucket_name = current_app.config["S3_STATIC_SITE_BUCKET"]
        bucket = s3.Bucket(bucket_name)

        try:
            s3.Object(bucket_name, old_path).load()
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                current_app.logger.info("Object %s does not exist" % (old_path))
        else:
            s3.Object(bucket_name, new_path).copy_from(CopySource="%s/%s" % (bucket_name, old_path), ACL="public-read")

            s3.Object(bucket_name, old_path).copy_from(
                CopySource="%s/%s" % (bucket_name, old_path),
                ACL="public-read",
                WebsiteRedirectLocation="https://www.ethnicity-facts-figures.service.gov.uk/%s" % new_path,
            )

        for obj in bucket.objects.filter(Prefix=old_path):
            new_object_path = obj.key.replace(old_path, new_path)

            # copy only latest to avoid having timeout issues
            # all other documents will be created with the build static script
            if obj.key.endswith("latest"):

                s3.Object(bucket_name, new_object_path).copy_from(
                    CopySource="%s/%s" % (bucket_name, obj.key), ACL="public-read"
                )

                s3.Object(bucket_name, obj.key).copy_from(
                    CopySource="%s/%s" % (bucket_name, obj.key),
                    ACL="public-read",
                    WebsiteRedirectLocation="https://www.ethnicity-facts-figures.service.gov.uk/%s" % new_object_path,
                )

        current_app.logger.info("Objects from %s copied to %s" % (old_path, new_path))

        return True


page_service = PageService()

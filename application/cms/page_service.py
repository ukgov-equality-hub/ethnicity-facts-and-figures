from datetime import datetime, date

from slugify import slugify
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import PageUnEditable, PageExistsException, PageNotFoundException, StaleUpdateException
from application.cms.models import (
    LowestLevelOfGeography,
    MeasureVersion,
    Measure,
    Subtopic,
    Topic,
    publish_status,
    DataSource,
)
from application.cms.service import Service
from application.utils import generate_review_token


class PageService(Service):
    def __init__(self):
        super().__init__()

    def update_page(self, page, data, last_updated_by, data_source_forms=None):
        if page.not_editable():
            message = "Error updating '{}' pages not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        elif page_service.is_stale_update(data, page):
            raise StaleUpdateException("")
        else:
            measure = Measure.query.get(page.measure_id)

            # Possibly temporary to work out issue with data deletions
            message = "EDIT MEASURE: Current state of page: %s" % page.to_dict()
            self.logger.info(message)
            message = "EDIT MEASURE: Data posted to update page: %s" % data
            self.logger.info(message)

            subtopic = data.pop("subtopic", None)
            if subtopic is not None and page.parent.guid != subtopic:
                new_subtopic = page_service.get_page(subtopic)
                conflicting_url = [measure for measure in new_subtopic.children if measure.slug == page.slug]
                if conflicting_url:
                    message = "A page with url %s already exists in %s" % (page.slug, new_subtopic.title)
                    raise PageExistsException(message)
                else:
                    page.parent = new_subtopic
                    page.position = len(new_subtopic.children)

                    topic = Topic.query.filter_by(slug=page.parent.parent.slug).one()
                    measure.subtopics = [Subtopic.query.filter_by(topic_id=topic.id, slug=new_subtopic.slug).one()]
                    measure.position = page.position

            data.pop("guid", None)
            title = data.pop("title").strip()
            if page.version == "1.0":
                slug = slugify(title)

                if slug != page.slug and self.new_slug_invalid(page, slug):
                    message = "The title '%s' and slug '%s' already exists under '%s'" % (title, slug, page.parent_guid)
                    raise PageExistsException(message)
                page.slug = slug
                page.measure.slug = slug

            page.title = title

            self._set_main_fields(page=page, data=data)
            self._set_data_sources(page=page, data_source_forms=data_source_forms)

            # Copy data to normalised `measure`
            if "internal_reference" in data:
                reference = data["internal_reference"]
                measure.reference = reference if reference else None

            if page.publish_status() in ["REJECTED", "UNPUBLISHED"]:
                new_status = publish_status.inv[1]
                page.status = new_status

            page.updated_at = datetime.utcnow()
            page.last_updated_by = last_updated_by

            db.session.commit()

            return page

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

    def get_page(self, guid):
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

    def get_page_with_version(self, guid, version):
        try:
            page = MeasureVersion.query.filter_by(guid=guid, version=version).one()

            # Temporary logging to work out issue with data deletions
            message = "Get page with version %s" % page.to_dict()
            self.logger.info(message)

            return page
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def reject_page(self, page_guid, version):
        page = self.get_page_with_version(page_guid, version)
        message = page.reject()
        db.session.commit()
        self.logger.info(message)
        return message

    def unpublish(self, page_guid, version, unpublished_by):
        page = self.get_page_with_version(page_guid, version)
        message = page.unpublish()
        page.unpublished_by = unpublished_by
        db.session.commit()
        self.logger.info(message)
        return (page, message)

    def send_page_to_draft(self, page_guid, version):
        page = self.get_page_with_version(page_guid, version)
        available_actions = page.available_actions()
        if "RETURN_TO_DRAFT" in available_actions:
            numerical_status = page.publish_status(numerical=True)
            page.status = publish_status.inv[(numerical_status + 1) % 6]
            page_service.save_page(page)
            message = 'Sent page "{}" back to {}'.format(page.title, page.status)
        else:
            message = 'Page "{}" can not be updated'.format(page.title)
        return message

    def mark_page_published(self, page):
        if page.published_at is None:
            page.published_at = date.today()
        page.published = True
        page.latest = True
        message = 'page "{}" published on "{}"'.format(page.guid, page.published_at.strftime("%Y-%m-%d"))
        self.logger.info(message)
        previous_version = page.get_previous_version()
        if previous_version and previous_version.latest:
            previous_version.latest = False
        db.session.commit()

    def delete_measure_page(self, measure, version):
        page = self.get_page_with_version(measure, version)
        previous_version = page.get_previous_version()
        if previous_version:
            previous_version.latest = True
        db.session.delete(page)
        db.session.commit()

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
    def get_pages_by_slug(subtopic, measure):
        return (
            MeasureVersion.query.filter_by(parent_guid=subtopic, slug=measure)
            .order_by(desc(MeasureVersion.version))
            .all()
        )

    @staticmethod
    def next_state(page, updated_by):
        message = page.next_state()
        page.last_updated_by = updated_by
        if page.status == "DEPARTMENT_REVIEW":
            page.review_token = generate_review_token(page.guid, page.version)
        if page.status == "APPROVED":
            page.published_by = updated_by
        db.session.commit()
        return message

    @staticmethod
    def save_page(page):
        db.session.add(page)
        db.session.commit()

    @staticmethod
    def get_latest_measures(subtopic):
        filtered = []
        seen = set([])
        for m in subtopic.children:
            if m.guid not in seen and m.latest:
                filtered.append(m)
                seen.add(m.guid)

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

    @staticmethod
    def new_slug_invalid(page, slug):
        existing_page = MeasureVersion.query.filter_by(slug=slug, parent_guid=page.parent_guid).first()
        if existing_page:
            return True
        else:
            return False

    @staticmethod
    def is_stale_update(data, page):
        update_db_version_id = int(data.pop("db_version_id"))
        if update_db_version_id < page.db_version_id:
            return page_service.page_and_data_have_diffs(data, page)
        else:
            return False

    @staticmethod
    def page_and_data_have_diffs(data, page):
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

    @staticmethod
    def set_lowest_level_of_geography(page, data):
        lowest_level_of_geography_id = data.pop("lowest_level_of_geography_id", None)
        if lowest_level_of_geography_id != "None" and lowest_level_of_geography_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            geography = LowestLevelOfGeography.query.get(lowest_level_of_geography_id)
            page.lowest_level_of_geography = geography

    @staticmethod
    def set_other_fields(data, page):
        for key, value in data.items():
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    value = None
            setattr(page, key, value)

    def _set_main_fields(self, page, data):
        try:
            self.set_lowest_level_of_geography(page, data)
        except NoResultFound:
            message = "There was an error setting lowest level of geography"
            self.logger.exception(message)
            raise PageUnEditable(message)

        self.set_other_fields(data, page)


page_service = PageService()

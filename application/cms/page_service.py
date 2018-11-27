import uuid
from datetime import datetime, date

from slugify import slugify
from sqlalchemy import desc
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import (
    DimensionNotFoundException,
    InvalidPageHierarchy,
    PageUnEditable,
    PageExistsException,
    PageNotFoundException,
    UpdateAlreadyExists,
    StaleUpdateException,
    UploadNotFoundException,
)
from application.cms.models import (
    FrequencyOfRelease,
    LowestLevelOfGeography,
    Organisation,
    Page,
    publish_status,
    TypeOfData,
    UKCountry,
    DataSource,
)
from application.cms.service import Service
from application.cms.upload_service import upload_service
from application.utils import generate_review_token, create_guid, get_bool

# Used to convert string values submitted for checkboxes in forms into the corresponding object value
# I know it's horrible, but it's the least bad way I've found to do it so far.
CHECKBOX_ENUM_LOOKUPS = {
    "TypeOfData.ADMINISTRATIVE": TypeOfData.ADMINISTRATIVE,
    "TypeOfData.SURVEY": TypeOfData.SURVEY,
    "UKCountry.ENGLAND": UKCountry.ENGLAND,
    "UKCountry.NORTHERN_IRELAND": UKCountry.NORTHERN_IRELAND,
    "UKCountry.SCOTLAND": UKCountry.SCOTLAND,
    "UKCountry.WALES": UKCountry.WALES,
    "UKCountry.UK": UKCountry.UK,
}


class PageService(Service):
    def __init__(self):
        super().__init__()

    def create_page(self, page_type, parent, data, created_by, data_source_forms, version="1.0"):
        title = data.pop("title", "").strip()
        guid = str(uuid.uuid4())
        uri = slugify(title)

        # we'll have to check if user selected another subtopic and did not use one passed via url
        subtopic = data.pop("subtopic", None)
        if subtopic is not None and subtopic != parent.guid:
            parent = page_service.get_page(subtopic)

        cannot_be_created, message = self.page_cannot_be_created(parent.guid, uri)
        if cannot_be_created:
            raise PageExistsException(message)
        self.logger.info(message)

        page = Page(
            guid=guid,
            version=version,
            uri=uri,
            title=title,
            parent_guid=parent.guid,
            parent_version=parent.version,
            page_type=page_type,
            status=publish_status.inv[1],
            created_by=created_by,
            position=len([c for c in parent.children if c.latest]),
        )

        self._set_main_fields(page=page, data=data)
        self._set_data_sources(page=page, data_source_forms=data_source_forms)

        db.session.add(page)
        db.session.commit()

        previous_version = page.get_previous_version()
        if previous_version is not None:
            previous_version.latest = False
            db.session.add(previous_version)
            db.session.commit()

        return page

    def update_page(self, page, data, last_updated_by, data_source_forms=None):
        if page.not_editable():
            message = "Error updating '{}' pages not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        elif page_service.is_stale_update(data, page):
            raise StaleUpdateException("")
        else:
            # Possibly temporary to work out issue with data deletions
            message = "EDIT MEASURE: Current state of page: %s" % page.to_dict()
            self.logger.info(message)
            message = "EDIT MEASURE: Data posted to update page: %s" % data
            self.logger.info(message)

            subtopic = data.pop("subtopic", None)
            if subtopic is not None and page.parent.guid != subtopic:
                new_subtopic = page_service.get_page(subtopic)
                conflicting_url = [measure for measure in new_subtopic.children if measure.uri == page.uri]
                if conflicting_url:
                    message = "A page with url %s already exists in %s" % (page.uri, new_subtopic.title)
                    raise PageExistsException(message)
                else:
                    page.parent = new_subtopic
                    page.position = len(new_subtopic.children)

            data.pop("guid", None)
            title = data.pop("title").strip()
            if page.version == "1.0":
                uri = slugify(title)

                if uri != page.uri and self.new_uri_invalid(page, uri):
                    message = "The title '%s' and uri '%s' already exists under '%s'" % (title, uri, page.parent_guid)
                    raise PageExistsException(message)
                page.uri = uri

            page.title = title

            self._set_main_fields(page=page, data=data)
            self._set_data_sources(page=page, data_source_forms=data_source_forms)

            if page.publish_status() in ["REJECTED", "UNPUBLISHED"]:
                new_status = publish_status.inv[1]
                page.status = new_status

            page.updated_at = datetime.utcnow()
            page.last_updated_by = last_updated_by

            db.session.add(page)
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
            return Page.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_page_with_title(self, title):
        try:
            return Page.query.filter_by(title=title).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_page_by_uri_and_type(self, uri, page_type, version=None):
        try:
            query = Page.query.filter_by(uri=uri, page_type=page_type)

            if version:
                query = query.filter_by(version=version)

            return query.one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    @staticmethod
    def get_measure_page_versions(parent_guid, measure_uri):
        return Page.query.filter_by(parent_guid=parent_guid, uri=measure_uri).order_by(desc(Page.version)).all()

    def get_page_with_version(self, guid, version):
        try:
            page = Page.query.filter_by(guid=guid, version=version).one()

            # Temporary logging to work out issue with data deletions
            message = "Get page with version %s" % page.to_dict()
            self.logger.info(message)

            return page
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_measure_page_hierarchy(
        self, topic_uri, subtopic_uri, measure_uri, version, dimension_guid=None, upload_guid=None
    ):
        try:
            topic_page = page_service.get_page_by_uri_and_type(topic_uri, "topic")
            subtopic_page = page_service.get_page_by_uri_and_type(subtopic_uri, "subtopic")
            measure_page = page_service.get_page_by_uri_and_type(measure_uri, "measure", version=version)
            dimension_object = measure_page.get_dimension(dimension_guid) if dimension_guid else None
            upload_object = measure_page.get_upload(upload_guid) if upload_guid else None
        except PageNotFoundException:
            self.logger.exception("Page id: {} not found".format(measure_uri))
            raise InvalidPageHierarchy
        except UploadNotFoundException:
            self.logger.exception("Upload id: {} not found".format(upload_guid))
            raise InvalidPageHierarchy
        except DimensionNotFoundException:
            self.logger.exception("Dimension id: {} not found".format(dimension_guid))
            raise InvalidPageHierarchy

        # Check the topic and subtopics in the URL are the right ones for the measure
        if measure_page.parent != subtopic_page or measure_page.parent.parent != topic_page:
            raise InvalidPageHierarchy

        # Check the dimension belongs to the measure
        if dimension_object and (
            dimension_object.page_id != measure_page.guid or dimension_object.page_version != measure_page.version
        ):
            raise InvalidPageHierarchy

        # Check the upload belongs to the measure
        if upload_object and (
            upload_object.page_id != measure_page.guid or upload_object.page_version != measure_page.version
        ):
            raise InvalidPageHierarchy

        return_items = [topic_page, subtopic_page, measure_page]
        if dimension_object:
            return_items.append(dimension_object)
        if upload_object:
            return_items.append(upload_object)

        return (item for item in return_items)

    def reject_page(self, page_guid, version):
        page = self.get_page_with_version(page_guid, version)
        message = page.reject()
        db.session.add(page)
        db.session.commit()
        self.logger.info(message)
        return message

    def unpublish(self, page_guid, version, unpublished_by):
        page = self.get_page_with_version(page_guid, version)
        message = page.unpublish()
        page.unpublished_by = unpublished_by
        db.session.add(page)
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

    def get_latest_version(self, topic_uri, subtopic_uri, measure_uri):
        try:
            topic = Page.query.filter_by(uri=topic_uri).one()
            subtopic = Page.query.filter_by(uri=subtopic_uri, parent_guid=topic.guid).one()
            pages = Page.query.filter_by(uri=measure_uri, parent_guid=subtopic.guid).order_by(desc(Page.version)).all()
            if len(pages) > 0:
                return pages[0]
            else:
                raise NoResultFound()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def mark_page_published(self, page):
        if page.publication_date is None:
            page.publication_date = date.today()
        page.published = True
        page.latest = True
        message = 'page "{}" published on "{}"'.format(page.guid, page.publication_date.strftime("%Y-%m-%d"))
        self.logger.info(message)
        db.session.add(page)
        previous_version = page.get_previous_version()
        if previous_version and previous_version.latest:
            previous_version.latest = False
            db.session.add(previous_version)
        db.session.commit()

    def page_cannot_be_created(self, parent, uri):
        pages_by_uri = self.get_pages_by_uri(parent, uri)
        if pages_by_uri:
            message = 'Page title "%s" and uri "%s" already exists under "%s"' % (
                pages_by_uri[0].title,
                pages_by_uri[0].uri,
                pages_by_uri[0].parent_guid,
            )
            return True, message

        else:
            message = "Page with parent %s and uri %s does not exist" % (parent, uri)
            self.logger.info(message)

        return False, message

    def create_copy(self, page_guid, page_version, version_type, created_by):
        """
        WARNING: This method has side_effects: any existing references to the page being copied will point to
        references of the COPY after this function runs.
        
        This function should be removed in the future. A tech improvement ticket has been generated here:
        
        https://trello.com/c/DFmMmd9g/78
        """
        page = self.get_page_with_version(page_guid, page_version)
        next_version = page.next_version_number_by_type(version_type)

        if version_type != "copy" and self.already_updating(page.guid, next_version):
            raise UpdateAlreadyExists()

        dimensions = [dimension for dimension in page.dimensions]
        uploads = [upload for upload in page.uploads]
        data_sources = [data_source for data_source in page.data_sources]

        db.session.expunge(page)
        make_transient(page)
        original_guid = page.guid

        if version_type == "copy":
            page.guid = str(uuid.uuid4())
            page.title = f"COPY OF {page.title}"
            # Duplicate (URI + version) in the same subtopic would mean we can't resolve preview URLs to a single page
            while self.new_uri_invalid(page, page.uri):
                page.uri = f"{page.uri}-copy"
        page.version = next_version
        page.status = "DRAFT"
        page.created_by = created_by
        page.created_at = datetime.utcnow()
        page.publication_date = None
        page.published = False
        page.internal_edit_summary = None
        page.external_edit_summary = None
        page.latest = True

        for data_source in data_sources:
            page.data_sources.append(data_source.copy())

        for dimension in dimensions:
            page.dimensions.append(dimension.copy())

        for upload in uploads:
            file_name = upload.file_name
            db.session.expunge(upload)
            make_transient(upload)
            upload.guid = create_guid(file_name)
            page.uploads.append(upload)

        db.session.add(page)
        db.session.commit()

        previous_page = page.get_previous_version()
        if previous_page is not None:
            previous_page.latest = False
            db.session.add(previous_page)
            db.session.commit()

        upload_service.copy_uploads(page, page_version, original_guid)

        return page

    def already_updating(self, page, next_version):
        try:
            self.get_page_with_version(page, next_version)
            return True
        except PageNotFoundException:
            return False

    def delete_measure_page(self, measure, version):
        page = self.get_page_with_version(measure, version)
        previous_version = page.get_previous_version()
        if previous_version:
            previous_version.latest = True
            db.session.add(previous_version)
        db.session.delete(page)
        db.session.commit()

    @staticmethod
    def get_pages_by_type(page_type):
        return Page.query.filter_by(page_type=page_type).order_by(Page.title, desc(Page.version)).all()

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
    def get_pages_by_uri(subtopic, measure):
        return Page.query.filter_by(parent_guid=subtopic, uri=measure).order_by(desc(Page.version)).all()

    @staticmethod
    def set_area_covered(page, data):

        area_covered = []

        # Main CMS form has separate fields for each country
        if data.pop("england", False):
            area_covered.append(UKCountry.ENGLAND)

        if data.pop("wales", False):
            area_covered.append(UKCountry.WALES)

        if data.pop("scotland", False):
            area_covered.append(UKCountry.SCOTLAND)

        if data.pop("northern_ireland", False):
            area_covered.append(UKCountry.NORTHERN_IRELAND)

        if set(area_covered) == {UKCountry.ENGLAND, UKCountry.NORTHERN_IRELAND, UKCountry.SCOTLAND, UKCountry.WALES}:
            area_covered = [UKCountry.UK]

        if len(area_covered) == 0:
            page.area_covered = None
        else:
            page.area_covered = area_covered

    @staticmethod
    def next_state(page, updated_by):
        message = page.next_state()
        page.last_updated_by = updated_by
        if page.status == "DEPARTMENT_REVIEW":
            page.review_token = generate_review_token(page.guid, page.version)
        if page.status == "APPROVED":
            page.published_by = updated_by
        db.session.add(page)
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
        return versions[-1].publication_date if versions else measure.publication_date

    @staticmethod
    def get_pages_to_unpublish():
        return Page.query.filter_by(status="UNPUBLISH").all()

    @staticmethod
    def mark_pages_unpublished(pages):
        for page in pages:
            page.published = False
            page.publication_date = None
            page.status = "UNPUBLISHED"
            db.session.add(page)
            db.session.commit()

    @staticmethod
    def new_uri_invalid(page, uri):
        existing_page = Page.query.filter_by(uri=uri, parent_guid=page.parent_guid).first()
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
        self.set_area_covered(page, data)

        try:
            self.set_lowest_level_of_geography(page, data)
        except NoResultFound as e:
            message = "There was an error setting lowest level of geography"
            self.logger.exception(message)
            raise PageUnEditable(message)

        self.set_other_fields(data, page)


page_service = PageService()

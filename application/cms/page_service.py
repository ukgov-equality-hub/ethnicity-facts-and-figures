import uuid
from datetime import datetime, date

from slugify import slugify
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import (
    PageUnEditable,
    PageExistsException,
    PageNotFoundException,
    UpdateAlreadyExists,
    StaleUpdateException
)

from application.cms.models import (
    Page,
    publish_status,
    TypeOfData,
    UKCountry,
    Organisation,
    LowestLevelOfGeography
)

from application.cms.service import Service
from application.cms.upload_service import upload_service

from application.utils import (
    generate_review_token,
    create_guid
)


class PageService(Service):

    def __init__(self):
        super().__init__()

    def create_page(self, page_type, parent, data, created_by, version='1.0'):
        title = data.pop('title', '').strip()
        guid = str(uuid.uuid4())
        uri = slugify(title)

        # we'll have to check if user selected another subtopic and did not use one passed via url
        subtopic = data.pop('subtopic', None)
        if subtopic is not None and subtopic != parent.guid:
            parent = page_service.get_page(subtopic)

        cannot_be_created, message = self.page_cannot_be_created(parent.guid, uri)
        if cannot_be_created:
            raise PageExistsException(message)
        self.logger.info(message)

        page = Page(guid=guid,
                    version=version,
                    uri=uri,
                    title=title,
                    parent_guid=parent.guid,
                    parent_version=parent.version,
                    page_type=page_type,
                    status=publish_status.inv[1],
                    created_by=created_by,
                    position=len([c for c in parent.children if c.latest]))

        self._set_main_fields(data, page)

        page.internal_edit_summary = 'Initial version'
        page.external_edit_summary = 'First published'

        db.session.add(page)
        db.session.commit()

        previous_version = page.get_previous_version()
        if previous_version is not None:
            previous_version.latest = False
            db.session.add(previous_version)
            db.session.commit()

        return page

    def update_page(self, page, data, last_updated_by):
        if page.not_editable():
            message = "Error updating '{}' pages not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        elif page_service.is_stale_update(data, page):
            raise StaleUpdateException('')
        else:
            # Possibly temporary to work out issue with data deletions
            message = 'EDIT MEASURE: Current state of page: %s' % page.to_dict()
            self.logger.info(message)
            message = 'EDIT MEASURE: Data posted to update page: %s' % data
            self.logger.info(message)

            subtopic = data.pop('subtopic', None)
            if subtopic is not None and page.parent.guid != subtopic:
                new_subtopic = page_service.get_page(subtopic)
                conflicting_url = [measure for measure in new_subtopic.children if measure.uri == page.uri]
                if conflicting_url:
                    message = 'A page with url %s already exists in %s' % (page.uri, new_subtopic.title)
                    raise PageExistsException(message)
                else:
                    page.parent = new_subtopic
                    page.position = len(new_subtopic.children)

            data.pop('guid', None)
            title = data.pop('title').strip()
            if page.version == '1.0':
                uri = slugify(title)

                if uri != page.uri and self.new_uri_invalid(page, uri):
                    message = "The title '%s' and uri '%s' already exists under '%s'" % (title, uri, page.parent_guid)
                    raise PageExistsException(message)
                page.uri = uri

            page.title = title

            self._set_main_fields(data, page)

            if page.publish_status() in ["REJECTED", "UNPUBLISHED"]:
                new_status = publish_status.inv[1]
                page.status = new_status

            page.updated_at = datetime.utcnow()
            page.last_updated_by = last_updated_by

            db.session.add(page)
            db.session.commit()

            # Possibly temporary to work out issue with data deletions
            message = 'EDIT MEASURE: Page updated to: %s' % page.to_dict()
            self.logger.info(message)
            return page

    def get_page(self, guid):
        try:
            return Page.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_page_by_uri_and_type(self, uri, page_type):
        try:
            return Page.query.filter_by(uri=uri, page_type=page_type).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_page_with_version(self, guid, version):
        try:
            page = Page.query.filter_by(guid=guid, version=version).one()

            # Temporary logging to work out issue with data deletions
            message = 'Get page with version %s' % page.to_dict()
            self.logger.info(message)

            return page
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

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
        if 'RETURN_TO_DRAFT' in available_actions:
            numerical_status = page.publish_status(numerical=True)
            page.status = publish_status.inv[(numerical_status + 1) % 6]
            page_service.save_page(page)
            message = 'Sent page "{}" back to {}'.format(page.title, page.status)
        else:
            message = 'Page "{}" can not be updated'.format(page.title)
        return message

    def get_page_by_uri_and_version(self, subtopic, measure, version):
        try:
            return Page.query.filter_by(parent_guid=subtopic, uri=measure, version=version).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_latest_version(self, subtopic, measure):
        try:
            pages = Page.query.filter_by(parent_guid=subtopic, uri=measure).all()
            pages.sort(reverse=True)
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
        message = 'page "{}" published on "{}"'.format(page.guid, page.publication_date.strftime('%Y-%m-%d'))
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
            message = 'Page title "%s" and uri "%s" already exists under "%s"' % (pages_by_uri[0].title,
                                                                                  pages_by_uri[0].uri,
                                                                                  pages_by_uri[0].parent_guid)
            return True, message

        else:
            message = 'Page with parent %s and uri %s does not exist' % (parent, uri)
            self.logger.info(message)

        return False, message

    def create_copy(self, page_id, version, version_type, created_by):

        page = self.get_page_with_version(page_id, version)
        next_version = page.next_version_number_by_type(version_type)

        if self.already_updating(page.guid, next_version):
            raise UpdateAlreadyExists()

        dimensions = [d for d in page.dimensions]
        uploads = [d for d in page.uploads]

        db.session.expunge(page)
        make_transient(page)

        page.version = next_version
        page.status = 'DRAFT'
        page.created_by = created_by
        page.created_at = datetime.utcnow()
        page.publication_date = None
        page.published = False
        page.internal_edit_summary = None
        page.external_edit_summary = None
        page.latest = True

        for d in dimensions:
            db.session.expunge(d)
            make_transient(d)
            d.guid = create_guid(d.title)
            page.dimensions.append(d)

        for u in uploads:
            db.session.expunge(u)
            make_transient(u)
            u.guid = create_guid(u.file_name)
            page.uploads.append(u)

        db.session.add(page)
        db.session.commit()

        previous_page = page.get_previous_version()
        if previous_page is not None:
            previous_page.latest = False
            db.session.add(previous_page)
            db.session.commit()

        upload_service.copy_uploads(page, version)

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
    def get_measure_page_versions(parent_guid, guid):
        return Page.query.filter_by(parent_guid=parent_guid, guid=guid).all()

    @staticmethod
    def get_pages_by_type(page_type):
        return Page.query.filter_by(page_type=page_type).all()

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
        return Page.query.filter_by(parent_guid=subtopic, uri=measure).all()

    @staticmethod
    def set_type_of_data(page, data):

        type_of_data = []

        if data.pop('administrative_data', False):
            type_of_data.append(TypeOfData.ADMINISTRATIVE)

        if data.pop('survey_data', False):
            type_of_data.append(TypeOfData.SURVEY)

        page.type_of_data = type_of_data

    @staticmethod
    def set_area_covered(page, data):

        area_covered = []

        if data.pop('england', False):
            area_covered.append(UKCountry.ENGLAND)

        if data.pop('wales', False):
            area_covered.append(UKCountry.WALES)

        if data.pop('scotland', False):
            area_covered.append(UKCountry.SCOTLAND)

        if data.pop('northern_ireland', False):
            area_covered.append(UKCountry.NORTHERN_IRELAND)

        if len(area_covered) == 4:
            area_covered = [UKCountry.UK]
        if len(area_covered) == 0:
            page.area_covered = None
        else:
            page.area_covered = area_covered

    @staticmethod
    def next_state(page, updated_by):
        message = page.next_state()
        page.last_updated_by = updated_by
        if page.status == 'DEPARTMENT_REVIEW':
            page.review_token = generate_review_token(page.guid, page.version)
        if page.status == 'APPROVED':
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
        return Page.query.filter_by(status='UNPUBLISH').all()

    @staticmethod
    def mark_pages_unpublished(pages):
        for page in pages:
            page.published = False
            page.publication_date = None
            page.status = 'UNPUBLISHED'
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
        update_db_version_id = int(data.pop('db_version_id'))
        if update_db_version_id < page.db_version_id:
            return page_service.page_and_data_have_diffs(data, page)
        else:
            return False

    @staticmethod
    def page_and_data_have_diffs(data, page):
        for k, v in data.items():
            if hasattr(page, k) and k != 'db_version_id':
                page_value = getattr(page, k)
                if v != page_value and page_value.strip() != '':
                    return True
        return False

    @staticmethod
    def set_page_frequency(page, data):
        frequency_id = data.pop('frequency_id', None)
        if frequency_id != 'None' and frequency_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            page.frequency_id = frequency_id

        frequency_other = data.pop('frequency_other', None)
        if page.frequency_id and page.frequency_of_release is not None \
                and page.frequency_of_release.description == 'Other' and frequency_other is not None:
            page.frequency_other = frequency_other
        else:
            page.frequency_other = None

        secondary_source_1_frequency_id = data.pop('secondary_source_1_frequency_id', None)
        if secondary_source_1_frequency_id != 'None' and secondary_source_1_frequency_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            page.secondary_source_1_frequency_id = secondary_source_1_frequency_id

        secondary_source_1_frequency_other = data.pop('secondary_source_1_frequency_other', None)
        if page.secondary_source_1_frequency_id \
                and page.secondary_source_1_frequency is not None \
                and page.secondary_source_1_frequency_of_release.description == 'Other' \
                and secondary_source_1_frequency_other is not None:
            page.secondary_source_1_frequency_other = secondary_source_1_frequency_other
        else:
            page.secondary_source_1_frequency_other = None

        secondary_source_2_frequency_id = data.pop('secondary_source_2_frequency_id', None)
        if secondary_source_2_frequency_id != 'None' and secondary_source_2_frequency_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            page.secondary_source_2_frequency_id = secondary_source_2_frequency_id

        secondary_source_2_frequency_other = data.pop('secondary_source_2_frequency_other', None)
        if page.secondary_source_2_frequency_id \
                and page.secondary_source_2_frequency_of_release \
                and page.secondary_source_2_frequency_of_release.description == 'Other' \
                and secondary_source_2_frequency_other is not None:
            page.secondary_source_2_frequency_other = secondary_source_2_frequency_other
        else:
            page.secondary_source_2_frequency_other = None

    @staticmethod
    def set_department_source(page, data):
        dept_id = data.pop('department_source', None)
        if dept_id is not None:
            dept = Organisation.query.get(dept_id)
            page.department_source = dept

        secondary_source_1_publisher = data.pop('secondary_source_1_publisher', None)
        if secondary_source_1_publisher is not None:
            secondary_source_1_publisher = Organisation.query.get(secondary_source_1_publisher)
            page.secondary_source_1_publisher = secondary_source_1_publisher

        secondary_source_2_publisher = data.pop('secondary_source_2_publisher', None)
        if secondary_source_2_publisher is not None:
            secondary_source_2_publisher = Organisation.query.get(secondary_source_2_publisher)
            page.secondary_source_2_publisher = secondary_source_2_publisher

    @staticmethod
    def set_lowest_level_of_geography(page, data):
        lowest_level_of_geography_id = data.pop('lowest_level_of_geography_id', None)
        if lowest_level_of_geography_id != 'None' and lowest_level_of_geography_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            geography = LowestLevelOfGeography.query.get(lowest_level_of_geography_id)
            page.lowest_level_of_geography = geography

    @staticmethod
    def set_other_fields(data, page):
        for key, value in data.items():
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    value = None
            setattr(page, key, value)

    def _set_main_fields(self, data, page):

        self.set_type_of_data(page, data)
        self.set_area_covered(page, data)

        try:
            self.set_lowest_level_of_geography(page, data)
        except NoResultFound as e:
            message = "There was an error setting lowest level of geography"
            self.logger.exception(message)
            raise PageUnEditable(message)
        try:
            self.set_page_frequency(page, data)
        except NoResultFound as e:
            message = "There was an error setting frequency of publication"
            self.logger.exception(message)
            raise PageUnEditable(message)
        try:
            self.set_department_source(page, data)
        except NoResultFound as e:
            message = "There was an error setting the department source (publisher) of the data"
            self.logger.exception(message)
            raise PageUnEditable(message)

        self.set_other_fields(data, page)


page_service = PageService()

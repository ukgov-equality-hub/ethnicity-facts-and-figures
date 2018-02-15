import hashlib
import json
import logging
import os
import tempfile
import time
import subprocess

from datetime import datetime, date

from flask import current_app
from slugify import slugify
from sqlalchemy import null
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from application import db
from application.cms.category_service import category_service
from application.cms.data_utils import DataProcessor
from application.cms.exceptions import (
    PageUnEditable,
    DimensionAlreadyExists,
    DimensionNotFoundException,
    PageExistsException,
    PageNotFoundException,
    UploadNotFoundException,
    UploadAlreadyExists,
    UpdateAlreadyExists,
    UploadCheckPending,
    UploadCheckError,
    UploadCheckFailed,
    StaleUpdateException
)

from application.cms.models import (
    Page,
    publish_status,
    Dimension,
    Upload,
    TypeOfData,
    UKCountry,
    Organisation,
    LowestLevelOfGeography
)

from application.utils import (
    setup_module_logging,
    generate_review_token
)

logger = logging.Logger(__name__)


class PageService:

    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised page service')

    def create_page(self, page_type, parent, data, created_by, version='1.0'):
        title = data.pop('title', '').strip()
        guid = data.pop('guid').strip().replace(' ', '')
        uri = slugify(title)

        if parent is not None:
            cannot_be_created, message = self.page_cannot_be_created(guid, parent.guid, uri)
            if cannot_be_created:
                raise PageExistsException(message)

        self.logger.info('No page with guid %s exists. OK to create', guid)
        db_page = Page(guid=guid,
                       version=version,
                       uri=uri,
                       title=title,
                       parent_guid=parent.guid if parent is not None else None,
                       parent_version=parent.version if parent is not None else None,
                       page_type=page_type,
                       status=publish_status.inv[1],
                       created_by=created_by)

        for key, val in data.items():
            if isinstance(val, str):
                val = val.strip()
            setattr(db_page, key, val)

        db_page.internal_edit_summary = 'Initial version'
        db_page.external_edit_summary = 'First published'

        db.session.add(db_page)
        db.session.commit()
        return db_page

    def get_topics(self):
        return Page.query.filter_by(page_type='topic').all()

    def get_pages(self):
        return Page.query.all()

    def get_pages_by_type(self, page_type):
        return Page.query.filter_by(page_type=page_type).all()

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

    @staticmethod
    def get_measure_page_versions(parent_guid, guid):
        return Page.query.filter_by(parent_guid=parent_guid, guid=guid).all()

    def get_page_with_version(self, guid, version):
        try:
            return Page.query.filter_by(guid=guid, version=version).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def create_dimension(self,
                         page,
                         title,
                         time_period,
                         summary,
                         ethnicity_category,
                         include_parents=False,
                         include_all=False,
                         include_unknown=False):

        guid = PageService.create_guid(title)

        if not self.check_dimension_title_unique(page, title):
            raise DimensionAlreadyExists()
        else:
            self.logger.info('Dimension with guid %s does not exist ok to proceed', guid)

            db_dimension = Dimension(guid=guid,
                                     title=title,
                                     time_period=time_period,
                                     summary=summary,
                                     page=page,
                                     position=page.dimensions.count())

            page.dimensions.append(db_dimension)
            db.session.add(page)
            db.session.commit()

            if ethnicity_category and ethnicity_category != '':
                category = category_service.get_category_by_id(ethnicity_category)
                category_service.link_category_to_dimension(db_dimension, 'Ethnicity', category.title,
                                                            include_parents, include_all, include_unknown)

            return page.get_dimension(db_dimension.guid)

    @staticmethod
    def create_guid(value):
        hash = hashlib.sha1()
        hash.update("{}{}".format(str(time.time()), slugify(value)).encode('utf-8'))
        return hash.hexdigest()

    def update_measure_dimension(self, measure_page, dimension, post_data):
        if measure_page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        data = {}
        if 'chartObject' in post_data:
            data['chart'] = post_data['chartObject']
            data['chart_source_data'] = post_data['source']

        if 'tableObject' in post_data:
            data['table'] = post_data['tableObject']
            data['table_source_data'] = post_data['source']

        page_service.update_dimension(dimension, data)

    def edit_upload(self, measure, upload, data, file=None):
        if measure.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        page_file_system = current_app.file_service.page_system(measure)

        new_title = data.get('title', upload.title)
        existing_title = upload.title

        if file:
            if new_title:
                extension = file.filename.split('.')[-1]
                file_name = "%s.%s" % (slugify(data['title']), extension)
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                file.size = size
                self.upload_data(measure, file, filename=file_name)
                if upload.file_name != file_name:
                    self.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file_name
            else:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                file.size = size
                self.upload_data(measure, file, filename=file.filename)
                if upload.file_name != file.filename:
                    self.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file.filename
        else:
            if new_title != existing_title:  # current file needs renaming
                extension = upload.file_name.split('.')[-1]
                file_name = "%s.%s" % (slugify(data['title']), extension)
                if current_app.config.get('FILE_SERVICE', 'local').lower() == 'local':
                    path = page_service.get_url_for_file(measure, upload.file_name)
                    dir_path = os.path.dirname(path)
                    page_file_system.rename_file(upload.file_name, file_name, dir_path)
                else:
                    if data['title'] != upload.title:
                        path = '%s/%s/source' % (measure.guid, measure.version)
                        page_file_system.rename_file(upload.file_name, file_name, path)
                self.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file_name

        upload.description = data['description'] if 'description' in data else upload.title
        upload.title = new_title

        db.session.add(upload)
        db.session.commit()

    def delete_dimension(self, page, guid):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        dimension = page.get_dimension(guid)

        db.session.delete(dimension)
        db.session.commit()

    def delete_upload_obj(self, page, guid):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        upload = page.get_upload(guid)
        try:
            self.delete_upload_files(page=page, file_name=upload.file_name)
        except FileNotFoundError:
            pass

        db.session.delete(upload)
        db.session.commit()

    def update_dimension(self, dimension, data):
        dimension.title = data['title'] if 'title' in data else dimension.title
        dimension.time_period = data['time_period'] if 'time_period' in data else dimension.time_period
        dimension.summary = data['summary'] if 'summary' in data else dimension.summary
        dimension.chart = data['chart'] if 'chart' in data else dimension.chart
        dimension.table = data['table'] if 'table' in data else dimension.table
        if dimension.chart and data.get('chart_source_data') is not None:
            chart_options = data.get('chart_source_data').get('chartOptions')
            for key, val in chart_options.items():
                if val is None:
                    chart_options[key] = '[None]'
            data['chart_source_data']['chartOptions'] = chart_options
            dimension.chart_source_data = data.get('chart_source_data')

        if dimension.table and data.get('table_source_data') is not None:
            table_options = data.get('table_source_data').get('tableOptions')
            for key, val in table_options.items():
                if val is None:
                    table_options[key] = '[None]'
            data['table_source_data']['tableOptions'] = table_options
            dimension.table_source_data = data.get('table_source_data')

        db.session.add(dimension)
        db.session.commit()

        if 'ethnicity_category' in data:
            # Remove current value
            category_service.unlink_dimension_from_family(dimension, 'Ethnicity')
            if data['ethnicity_category'] != '':
                # Add new value
                category = category_service.get_category_by_id(data['ethnicity_category'])
                category_service.link_category_to_dimension(dimension, 'Ethnicity',
                                                            category.title,
                                                            data['include_parents'],
                                                            data['include_all'],
                                                            data['include_unknown'])

    @staticmethod
    def delete_chart(dimension):
        dimension.chart = null()
        dimension.chart_source_data = null()
        db.session.add(dimension)
        db.session.commit()

    @staticmethod
    def delete_table(dimension):
        dimension.table = null()
        dimension.table_source_data = null()
        db.session.add(dimension)
        db.session.commit()

    def set_dimension_positions(self, dimension_positions):
        for item in dimension_positions:
            try:
                dimension = Dimension.query.filter_by(guid=item['guid']).one()
                dimension.position = item['index']
                db.session.add(dimension)
            except NoResultFound as e:
                self.logger.exception(e)
                raise DimensionNotFoundException()
        if db.session.dirty:
            db.session.commit()

    def get_upload(self, page, file_name):
        try:
            upload = Upload.query.filter_by(page=page, file_name=file_name).one()
            return upload
        except NoResultFound as e:
            self.logger.exception(e)
            raise UploadNotFoundException()

    def check_dimension_title_unique(self, page, title):
        try:
            Dimension.query.filter_by(page=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    def check_upload_title_unique(self, page, title):
        try:
            Upload.query.filter_by(page=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    def update_page(self, page, data, last_updated_by):
        if page.not_editable():
            message = "Error updating '{}' pages not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        elif page_service.is_stale_update(data, page):
            raise StaleUpdateException('')
        else:
            data.pop('guid', None)
            title = data.pop('title').strip()
            uri = slugify(title)

            if uri != page.uri and self.new_uri_invalid(page, uri):
                message = "The title '%s' and uri '%s' already exists under '%s'" % (title, uri, page.parent_guid)
                raise PageExistsException(message)

            page.title = title
            page.uri = uri

            self.set_type_of_data(page, data)
            self.set_area_covered(page, data)
            self.set_lowest_level_of_geography(page, data)

            try:
                self.set_page_frequency(page, data)
            except NoResultFound as e:
                message = "There was an error setting frequency of publication"
                raise PageUnEditable(message)

            try:
                self.set_department_source(page, data)
            except NoResultFound as e:
                message = "There was an error setting the department source (publisher) of the data"
                raise PageUnEditable(message)

            for key, value in data.items():
                if isinstance(value, str):
                    value = value.strip()
                setattr(page, key, value)

            if page.publish_status() in ["REJECTED", "UNPUBLISHED"]:
                new_status = publish_status.inv[1]
                page.status = new_status

            page.updated_at = datetime.utcnow()
            page.last_updated_by = last_updated_by

        db.session.add(page)
        db.session.commit()

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

    def next_state(self, page, updated_by):
        message = page.next_state()
        page.last_updated_by = updated_by
        if page.status == 'DEPARTMENT_REVIEW':
            page.review_token = generate_review_token(page.guid, page.version)
        if page.status == 'APPROVED':
            page.published_by = updated_by
        db.session.add(page)
        db.session.commit()
        return message

    def save_page(self, page):
        db.session.add(page)
        db.session.commit()

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
            message = 'Sent page "{}" id: {} back to {}'.format(page.title, page.guid, page.status)
        else:
            message = 'Page "{}" id: {} can not be updated'.format(page.title, page.guid)
        return message

    def upload_data(self, page, file, filename=None):
        page_file_system = current_app.file_service.page_system(page)
        if not filename:
            filename = file.name
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file = '%s/%s' % (tmpdirname, filename)
            file.save(tmp_file)
            self.validate_file(tmp_file)
            if current_app.config['ATTACHMENT_SCANNER_ENABLED']:
                attachment_scanner_url = current_app.config['ATTACHMENT_SCANNER_API_URL']
                attachment_scanner_key = current_app.config['ATTACHMENT_SCANNER_API_KEY']
                x = subprocess.check_output(["curl",
                                             "--request", "POST",
                                             "--url", attachment_scanner_url,
                                             "--header", "authorization: bearer %s" % attachment_scanner_key,
                                             "--header", "content-type: multipart/form-data",
                                             "--form", "file=@%s" % tmp_file])
                response = json.loads(x.decode("utf-8"))
                if response["status"] == "ok":
                    pass
                elif response["status"] == "pending":
                    raise UploadCheckPending("Upload check did not complete, you can check back later, see docs")
                elif response["status"] == "failed":
                    raise UploadCheckFailed("Upload check could not be completed, an error occurred.")
                elif response["status"] == "found":
                    raise UploadCheckError("Virus scan has found something suspicious.")
            page_file_system.write(tmp_file, 'source/%s' % secure_filename(filename))
        return page_file_system

    def validate_file(self, filename):
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
        detector.reset()

        with open(filename, 'rb') as to_convert:
            for line in to_convert:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            encoding = detector.result.get('encoding')
        valid_encodings = ['ascii', 'iso-8859-1', 'utf-8']
        if encoding is None:
            message = 'File encoding could not be detected'
            self.logger.exception(message)
            raise UploadCheckError(message)
        if encoding.lower() not in valid_encodings:
            message = 'File encoding %s not valid. Valid encodings: %s' % (encoding, valid_encodings)
            self.logger.exception(message)
            raise UploadCheckError(message)

    def create_upload(self, page, upload, title, description):
        extension = upload.filename.split('.')[-1]
        if title and extension:
            file_name = "%s.%s" % (slugify(title), extension)
        else:
            file_name = upload.filename

        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        guid = PageService.create_guid(file_name)

        if not self.check_upload_title_unique(page, title):
            raise UploadAlreadyExists('An upload with that title already exists for this measure')
        else:
            self.logger.info('Upload with guid %s does not exist ok to proceed', guid)
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            page_service.upload_data(page, upload, filename=file_name)
            db_upload = Upload(guid=guid,
                               title=title,
                               file_name=file_name,
                               description=description,
                               page=page,
                               size=size)

            page.uploads.append(db_upload)
            db.session.add(page)
            db.session.commit()

        return db_upload

    @staticmethod
    def process_uploads(page):
        processor = DataProcessor()
        processor.process_files(page)

    @staticmethod
    def delete_upload_files(page, file_name):
        try:
            page_file_system = current_app.file_service.page_system(page)
            page_file_system.delete('source/%s' % file_name)
        except FileNotFoundError:
            pass

    @staticmethod
    def get_page_uploads(page):
        page_file_system = current_app.file_service.page_system(page)
        return page_file_system.list_files('data')

    @staticmethod
    def get_url_for_file(page, file_name, directory='data'):
        page_file_system = current_app.file_service.page_system(page)
        return page_file_system.url_for_file('%s/%s' % (directory, file_name))

    @staticmethod
    def get_measure_download(upload, file_name, directory):
        page_file_system = current_app.file_service.page_system(upload.page)
        output_file = tempfile.NamedTemporaryFile(delete=False)
        key = '%s/%s' % (directory, file_name)
        page_file_system.read(key, output_file.name)
        return output_file.name

    def get_pages_by_uri(self, subtopic, measure):
        return Page.query.filter_by(parent_guid=subtopic, uri=measure).all()

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
        message = 'page "{}" published on "{}"'.format(page.guid, page.publication_date.strftime('%Y-%m-%d'))
        self.logger.info(message)
        db.session.add(page)
        db.session.commit()

    def page_cannot_be_created(self, guid, parent, uri):
        try:
            page_by_guid = page_service.get_page(guid)
            message = 'Page with guid %s already exists' % page_by_guid.guid
            return True, message
        except PageNotFoundException:
            message = 'Page with guid %s does not exist' % guid
            self.logger.info(message)

        pages_by_uri = self.get_pages_by_uri(parent, uri)
        if pages_by_uri:
            message = 'Page title "%s" and uri "%s" already exists under "%s"' % (pages_by_uri[0].title,
                                                                                  pages_by_uri[0].uri,
                                                                                  pages_by_uri[0].parent_guid)
            return True, message

        else:
            message = 'Page with parent %s and uri %s does not exist' % (parent, uri)
            self.logger.info(message)

        return False, None

    def create_copy(self, page_id, version, version_type):

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
        page.created_at = datetime.utcnow()
        page.publication_date = None
        page.published = False
        page.internal_edit_summary = None
        page.external_edit_summary = None

        for d in dimensions:
            db.session.expunge(d)
            make_transient(d)
            d.guid = PageService.create_guid(d.title)
            page.dimensions.append(d)

        for u in uploads:
            db.session.expunge(u)
            make_transient(u)
            u.guid = PageService.create_guid(u.file_name)
            page.uploads.append(u)

        db.session.add(page)
        db.session.commit()

        page_service.copy_uploads(page, version)

        return page

    def already_updating(self, page, next_version):
        try:
            self.get_page_with_version(page, next_version)
            return True
        except PageNotFoundException:
            return False

    @staticmethod
    def get_latest_publishable_measures(subtopic, publication_states):
        filtered = []
        seen = set([])
        for m in subtopic.children:
            if m.guid not in seen:
                versions = m.get_versions()
                versions.sort(reverse=True)
                for v in versions:
                    if v.eligible_for_build(publication_states):
                        filtered.append(v)
                        seen.add(v.guid)
                        break
        return filtered

    @staticmethod
    def get_latest_measures(subtopic):
        filtered = []
        seen = set([])
        for m in subtopic.children:
            if m.guid not in seen and m.is_latest():
                filtered.append(m)
                seen.add(m.guid)
        return filtered

    def delete_measure_page(self, measure, version):
        page = self.get_page_with_version(measure, version)
        db.session.delete(page)
        db.session.commit()

    @staticmethod
    def copy_uploads(page, old_version):
        page_file_system = current_app.file_service.page_system(page)
        from_key = '%s/%s/source' % (page.guid, old_version)
        to_key = '%s/%s/source' % (page.guid, page.version)
        for upload in page.uploads:
            from_path = '%s/%s' % (from_key, upload.file_name)
            to_path = '%s/%s' % (to_key, upload.file_name)
            page_file_system.copy_file(from_path, to_path)

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
    def get_latest_version_of_newer_edition(measure):
        versions_in_different_editions = []

        versions = measure.get_versions(include_self=False)
        versions.sort(reverse=True)

        for version in versions:
            if version.major() > measure.major():
                versions_in_different_editions.append(version)

        if len(versions_in_different_editions) > 0:
            return versions_in_different_editions[0]
        else:
            return None

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
        if page.frequency_id and page.frequency_of_release.description == 'Other' and frequency_other is not None:
            page.frequency_other = frequency_other
        else:
            page.frequency_other = None

    @staticmethod
    def set_department_source(page, data):
        dept_id = data.pop('department_source', None)
        if dept_id is not None:
            dept = Organisation.query.get(dept_id)
            page.department_source = dept

    @staticmethod
    def set_lowest_level_of_geography(page, data):
        lowest_level_of_geography_id = data.pop('lowest_level_of_geography_id', None)
        if lowest_level_of_geography_id != 'None' and lowest_level_of_geography_id is not None:
            # Note wtforms radio fields have the value 'None' - a string - if none selected
            geography = LowestLevelOfGeography.query.get(lowest_level_of_geography_id)
            page.lowest_level_of_geography = geography


page_service = PageService()

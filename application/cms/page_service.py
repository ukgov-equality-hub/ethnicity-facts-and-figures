import hashlib
import logging
import os
import tempfile
import time
from datetime import datetime, date

from copy import deepcopy, copy
from flask import current_app
from slugify import slugify
from sqlalchemy import null
from sqlalchemy.orm import make_transient
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from application import db
from application.cms.data_utils import DataProcessor
from application.cms.exceptions import (
    PageUnEditable,
    DimensionAlreadyExists,
    DimensionNotFoundException,
    PageExistsException,
    PageNotFoundException,
    UploadNotFoundException,
    UploadAlreadyExists,
    UpdateAlreadyExists)

from application.cms.models import (
    DbPage,
    publish_status,
    DbDimension,
    DbUpload
)

from application.utils import setup_module_logging

logger = logging.Logger(__name__)


class PageService:
    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised page service')

    def create_page(self, page_type, parent, data):
        title = data['title']
        guid = data.pop('guid')
        uri = slugify(title)

        if parent is not None:
            cannot_be_created, message = page_service.page_cannot_be_created(guid, parent.guid, uri)
            if cannot_be_created:
                raise PageExistsException(message)

        self.logger.info('No page with guid %s exists. OK to create', guid)
        db_page = DbPage(guid=guid,
                         version='1.0',
                         uri=uri,
                         parent_guid=parent.guid if parent is not None else None,
                         parent_version=parent.version if parent is not None else None,
                         page_type=page_type,
                         status=publish_status.inv[1])

        for key, val in data.items():
            setattr(db_page, key, val)

        db.session.add(db_page)
        db.session.commit()
        return db_page

    def get_topics(self):
        return DbPage.query.filter_by(page_type='topic').all()

    def get_pages(self):
        return DbPage.query.all()

    def get_pages_by_type(self, page_type):
        return DbPage.query.filter_by(page_type=page_type).all()

    def get_page(self, guid):
        try:
            return DbPage.query.filter_by(guid=guid).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    @staticmethod
    def get_measure_page_versions(parent_guid, guid):
        return DbPage.query.filter_by(parent_guid=parent_guid, guid=guid).order_by(DbPage.created_at).all()

    def get_page_with_version(self, guid, version):
        try:
            return DbPage.query.filter_by(guid=guid, version=version).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    # TODO add error handling for db update
    def create_dimension(self, page, title, time_period, summary, suppression_rules, disclosure_control,
                         type_of_statistic, location, source):

        guid = PageService.create_guid(title)

        if not self.check_dimension_title_unique(page, title):
            raise DimensionAlreadyExists()
        else:
            self.logger.info('Dimension with guid %s does not exist ok to proceed', guid)

            db_dimension = DbDimension(guid=guid,
                                       title=title,
                                       time_period=time_period,
                                       summary=summary,
                                       suppression_rules=suppression_rules,
                                       disclosure_control=disclosure_control,
                                       type_of_statistic=type_of_statistic,
                                       location=location,
                                       source=source,
                                       measure=page,
                                       position=page.dimensions.count())

            page.dimensions.append(db_dimension)
            db.session.add(page)
            db.session.commit()
            return db_dimension

    @staticmethod
    def create_guid(value):
        hash = hashlib.sha1()
        hash.update("{}{}".format(str(time.time()), slugify(value)).encode('utf-8'))
        return hash.hexdigest()

    # TODO add error handling for db update
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

    def edit_measure_upload(self, measure, upload, data, file=None):
        if measure.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        page_file_system = current_app.file_service.page_system(measure)

        if 'title' in data and not file:
            # Rename file
            extension = upload.file_name.split('.')[-1]
            file_name = "%s.%s" % (slugify(data['title']), extension)

            # TODO Refactor this into a rename_file method
            if current_app.config['FILE_SERVICE'] == 'local' or current_app.config['FILE_SERVICE'] == 'Local':
                path = page_service.get_url_for_file(measure, upload.file_name)
                dir_path = os.path.dirname(path)
                page_file_system.rename_file(upload.file_name, file_name, dir_path)
            else:  # S3
                if data['title'] != upload.title:
                    path = '%s/%s/data' % (measure.guid, measure.version)
                    page_file_system.rename_file(upload.file_name, file_name, path)

        if 'title' in data:
            upload.title = data['title']
            # Delete old file
            upload.file_name = file_name
        elif file:
            # Upload new file
            extension = upload.filename.split('.')[-1]
            file_name = "%s.%s" % (data['title'], extension)
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            upload.size = size
            self.upload_data(measure.guid, file, filename=file_name)
            # Delete old file
            self.delete_upload_files(page=measure, file_name=upload.file_name)
            upload.file_name = file_name

        upload.description = data['description'] if 'description' in data else upload.title

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

    # TODO add error handling for db update
    def update_dimension(self, dimension, data):
        dimension.title = data['title'] if 'title' in data else dimension.title
        dimension.time_period = data['time_period'] if 'time_period' in data else dimension.time_period
        dimension.summary = data['summary'] if 'summary' in data else dimension.summary
        dimension.chart = data['chart'] if 'chart' in data else dimension.chart
        dimension.table = data['table'] if 'table' in data else dimension.table
        dimension.suppression_rules = data['suppression_rules'] \
            if 'suppression_rules' in data else dimension.suppression_rules
        dimension.disclosure_control = data['disclosure_control'] \
            if 'disclosure_control' in data else dimension.disclosure_control
        dimension.type_of_statistic = data['type_of_statistic'] \
            if 'type_of_statistic' in data else dimension.type_of_statistic
        dimension.location = data['location'] if 'location' in data else dimension.location
        dimension.source = data['source'] if 'source' in data else dimension.source

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
                dimension = DbDimension.query.filter_by(guid=item['guid']).one()
                dimension.position = item['index']
                db.session.add(dimension)
            except NoResultFound as e:
                self.logger.exception(e)
                raise DimensionNotFoundException()
        if db.session.dirty:
            db.session.commit()

    def get_upload(self, page, version, file_name):
        try:
            upload = DbUpload.query.filter_by(page_id=page, page_version=version, file_name=file_name).one()
            return upload
        except NoResultFound as e:
            self.logger.exception(e)
            raise UploadNotFoundException()

    def check_dimension_title_unique(self, page, title):
        try:
            DbDimension.query.filter_by(measure=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    def check_upload_title_unique(self, page, title):
        try:
            DbUpload.query.filter_by(measure=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    # TODO db error handling
    def update_page(self, page, data, message=None):
        if page.not_editable():
            message = "Error updating '{}' pages not in DRAFT, REJECT, UNPUBLISHED can't be edited".format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        else:
            for key, value in data.items():
                setattr(page, key, value)

            if page.publish_status() in ["REJECTED", "UNPUBLISHED"]:
                new_status = publish_status.inv[1]
                page.status = new_status

            page.updated_at = datetime.utcnow()

        db.session.add(page)
        db.session.commit()

    def next_state(self, page):
        message = page.next_state()
        db.session.add(page)
        db.session.commit()
        self.logger.info(message)
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

    def unpublish(self, page_guid, version):
        page = self.get_page_with_version(page_guid, version)
        message = page.unpublish()
        page.published = False
        db.session.add(page)
        db.session.commit()
        self.logger.info(message)
        return message

    def send_page_to_draft(self, page_guid, version):
        page = self.get_page_with_version(page_guid, version)
        available_actions = page.available_actions()
        if 'UPDATE' in available_actions:
            numerical_status = page.publish_status(numerical=True)
            page.status = publish_status.inv[(numerical_status + 1) % 5]
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
            page_file_system.write(tmp_file, 'source/%s' % secure_filename(filename))
            self.process_uploads(page)

        return page_file_system

    def create_upload(self, page, upload, title, description):
        extension = upload.filename.split('.')[-1]
        file_name = "%s.%s" % (slugify(title), extension)

        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        guid = PageService.create_guid(file_name)

        if not self.check_upload_title_unique(page, title):
            raise UploadAlreadyExists()
        else:
            self.logger.info('Upload with guid %s does not exist ok to proceed', guid)
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            page_service.upload_data(page, upload, filename=file_name)
            db_upload = DbUpload(guid=guid,
                                 title=title,
                                 file_name=file_name,
                                 description=description,
                                 measure=page,
                                 size=size)

            page.uploads.append(db_upload)
            db.session.add(page)
            db.session.commit()

        return db_upload

    def process_uploads(self, page):
        processor = DataProcessor()
        processor.process_files(page)

    def delete_upload_files(self, page, file_name):
        page_file_system = current_app.file_service.page_system(page)
        page_file_system.delete('source/%s' % file_name)
        self.process_uploads(page)

    def get_page_uploads(self, page):
        page_file_system = current_app.file_service.page_system(page)
        return page_file_system.list_files('data')

    def get_url_for_file(self, page, file_name, directory='data'):
        page_file_system = current_app.file_service.page_system(page)
        return page_file_system.url_for_file('%s/%s' % (directory, file_name))

    @staticmethod
    def get_measure_download(upload, file_name, directory):
        page_file_system = current_app.file_service.page_system(upload.measure)
        with tempfile.TemporaryDirectory() as tmp_dir:
            key = '%s/%s' % (directory, file_name)
            output_file = '%s/%s.processed' % (tmp_dir, file_name)
            page_file_system.read(key, output_file)
            f = open(output_file, 'rb')
            return f.read()

    def get_page_by_uri(self, subtopic, measure, version):
        try:
            return DbPage.query.filter_by(parent_guid=subtopic, uri=measure, version=version).one()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def get_latest_published_page(self, subtopic, measure, publication_states):
        try:
            pages = DbPage.query.filter_by(parent_guid=subtopic, uri=measure).all()
            pages.sort()
            pages = [page for page in pages if page.status in publication_states]
            if len(pages) > 0:
                return pages[-1]
            else:
                raise NoResultFound()
        except NoResultFound as e:
            self.logger.exception(e)
            raise PageNotFoundException()

    def mark_page_published(self, page):
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

        try:
            page_by_uri = self.get_page_by_uri(parent, uri, '1.0')
            message = 'Page with title "%s" already exists under "%s". Please change title' % (page_by_uri.title,
                                                                                               page_by_uri.parent_guid)
            return True, message

        except PageNotFoundException:
            message = 'Page with parent %s and uri %s does not exist' % (parent, uri)
            self.logger.info(message)

        return False, None

    def create_copy(self, page_id, version):

        page = self.get_page_with_version(page_id, version)
        next_version = page.next_minor_version()

        if self.already_updating(page.guid, next_version):
            raise UpdateAlreadyExists()

        dimensions = [d for d in page.dimensions]
        uploads = [d for d in page.uploads]

        db.session.expunge(page)
        make_transient(page)

        page.version = next_version
        page.status = 'DRAFT'
        page.created_at = datetime.utcnow()

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
        processed = set([])
        for m in subtopic.children:
            if m.guid not in processed:
                versions = m.get_versions()
                versions.sort(reverse=True)
                for v in versions:
                    if v.eligible_for_build(publication_states):
                        filtered.append(v)
                        processed.add(v.guid)
                        break
        return filtered

    def delete_measure_page(self, measure, version):
        page = self.get_page_with_version(measure, version)
        db.session.delete(page)
        db.session.commit()


page_service = PageService()

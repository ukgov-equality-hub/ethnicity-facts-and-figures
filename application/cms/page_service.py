import hashlib
import json
import os
import tempfile
import logging
import time

from datetime import date

import io
from flask import current_app
from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import FileMultiDict, FileStorage
from werkzeug.utils import secure_filename

from application.cms.data_utils import DataProcessor
from application.cms.exceptions import (
    PageUnEditable,
    DimensionAlreadyExists,
    DimensionNotFoundException,
    PageExistsException, PageNotFoundException)

from application.cms.models import (
    DbPage,
    publish_status,
    DbDimension, DbUpload)

from application import db
from application.utils import setup_module_logging

logger = logging.Logger(__name__)


class PageService:
    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised page service')

    def create_page(self, page_type, parent=None, data=None, user=None):
        # TODO: Check page_type is valid
        # TODO: Make default parent homepage
        title = data['title']
        guid = data.pop('guid')

        try:
            page = page_service.get_page(guid)
            self.logger.exception('Page with guid %s already exists', page.guid)
            raise PageExistsException()
        except PageNotFoundException:
            self.logger.info('No page with guid %s exists. OK to create', guid)
            db_page = DbPage(guid=guid, uri=slugify(title),
                             parent_guid=parent,
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

    # TODO add error handling for db update
    def create_dimension(self, page, title, time_period, summary, suppression_rules, disclosure_control,
                         type_of_statistic, location, source):

        hash = hashlib.sha1()
        hash.update("{}{}".format(str(time.time()), slugify(title)).encode('utf-8'))
        guid = hash.hexdigest()

        if not self.check_dimension_title_unique(page, title):
            raise DimensionAlreadyExists
        else:
            self.logger.exception('Dimension with guid %s does not exist ok to proceed', guid)

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

        if 'title' in data:
            upload.title = data['title']

        if 'title' in data and not file:
            # Rename file
            extension = upload.file_name.split('.')[-1]
            file_name = "%s.%s" % (slugify(data['title']), extension)
            path = page_service.get_url_for_file(measure.guid, upload.file_name)
            print(path)
            stream = open(path, "rb")
            file_storage = FileStorage(stream=stream, filename=path)
            self.upload_data(measure.guid, file_storage, filename=file_name)
            # Delete old file
            self.delete_upload_files(page_guid=measure.guid, file_name=upload.file_name)
            upload.file_name = file_name
        elif file:
            # Upload new file
            extension = upload.filename.split('.')[-1]
            file_name = "%s.%s" % (data['title'], extension)
            self.upload_data(measure.guid, file, filename=file_name)
            # Delete old file
            self.delete_upload_files(page_guid=measure.guid, file_name=upload.file_name)
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
            self.delete_upload_files(page_guid=page.guid, file_name=upload.file_name)
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
            dimension.chart_source_data = json.dumps(data.get('chart_source_data'))
        if dimension.table and data.get('table_source_data') is not None:
            dimension.table_source_data = json.dumps(data.get('table_source_data'))

        db.session.add(dimension)
        db.session.commit()

    def delete_chart(self, dimension):
        dimension.chart = None
        dimension.chart_source_data = None
        db.session.add(dimension)
        db.session.commit()

    def delete_table(self, dimension):
        dimension.table = None
        dimension.table_source_data = None
        db.session.add(dimension)
        db.session.commit()

    def get_dimension(self, page, guid):
        try:
            page = DbDimension.query.filter_by(guid=guid).one()
            return page
        except NoResultFound as e:
            self.logger.exception(e)
            raise DimensionNotFoundException

    def check_dimension_title_unique(self, page, title):
        try:
            DbDimension.query.filter_by(measure=page, title=title).one()
            return False
        except NoResultFound as e:
            return True

    # TODO db error handling
    def update_page(self, page, data, message=None):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        else:
            for key, value in data.items():
                setattr(page, key, value)

            if page.publish_status() == "REJECTED":
                new_status = publish_status.inv[1]
                page.status = new_status

        db.session.add(page)
        db.session.commit()

    # TODO db error handling
    def next_state(self, page):
        message = page.next_state()
        db.session.add(page)
        db.session.commit()
        self.logger.info(message)
        return message

    # TODO db error handling
    def save_page(self, page):
        db.session.add(page)
        db.session.commit()

    # TODO db error handling
    def reject_page(self, page):
        message = page.reject()
        db.session.add(page)
        db.session.commit()
        self.logger.info(message)
        return message

    def upload_data(self, page_guid, file, upload_type='page', filename=None):
        page_file_system = current_app.file_service.page_system(page_guid)
        if not filename:
            filename = file.name

        with tempfile.TemporaryDirectory() as tmpdirname:
            # if page level file write file and process else just write file
            if upload_type == 'page':
                tmp_file = '%s/%s' % (tmpdirname, filename)
                file.save(tmp_file)
                page_file_system.write(tmp_file, 'source/%s' % secure_filename(filename))
                self.process_uploads(page_guid)
            elif upload_type in ['chart', 'table']:
                subdir = '%s/dimension/%s' % (tmpdirname, upload_type)
                if not os.path.isdir(subdir):
                    os.makedirs(subdir)
                tmp_file = '%s/%s' % (subdir, file.filename)
                file.save(tmp_file)
                page_file_system.write(tmp_file, 'dimension/%s/%s' % (upload_type, secure_filename(file.filename)))

        return page_file_system

    def create_upload(self, page, upload, title, description):
        extension = upload.filename.split('.')[-1]
        file_name = "%s.%s" % (slugify(title), extension)

        hash = hashlib.sha1()
        hash.update("{}{}".format(str(time.time()), file_name).encode('utf-8'))
        guid = hash.hexdigest()

        # if not self.check_dimension_title_unique(page, title):
        #     raise DimensionAlreadyExists
        # else:
        self.logger.exception('Upload with guid %s does not exist ok to proceed', guid)
        page_service.upload_data(page.guid, upload, filename=file_name)
        db_upload = DbUpload(guid=guid,
                             title=title,
                             file_name=file_name,
                             description=description,
                             measure=page)

        page.uploads.append(db_upload)
        db.session.add(page)
        db.session.commit()

        return db_upload

    def process_uploads(self, page_guid):
        page = self.get_page(page_guid)
        processor = DataProcessor()
        processor.process_files(page)

    def delete_upload_files(self, page_guid, file_name):
        page_file_system = current_app.file_service.page_system(page_guid)
        page_file_system.delete('source/%s' % file_name)
        self.process_uploads(page_guid)

    def get_page_uploads(self, page_guid):
        page_file_system = current_app.file_service.page_system(page_guid)
        return page_file_system.list_files('data')

    def get_url_for_file(self, page_guid, file_name, directory='data'):
        page_file_system = current_app.file_service.page_system(page_guid)
        return page_file_system.url_for_file('%s/%s' % (directory, file_name))

    @staticmethod
    def get_dimension_download(dimension, file_name, directory, static_site_url):
        page_file_system = current_app.file_service.page_system(dimension.measure.guid)

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = '%s/%s' % (directory, file_name)
            output_file = '%s/%s.processed' % (tmp_dir, file_name)
            page_file_system.read(input_file, output_file)

            contents = ['Title: %s\n' % dimension.title,
                        'Location: %s\n' % dimension.location,
                        'Time period: %s\n' % dimension.time_period,
                        'Data source: %s\n' % dimension.source,
                        'Source: %s\n\n' % static_site_url
                        ]
            with open(output_file) as file:
                contents.extend(file.readlines())

            return ''.join(contents)

    def get_page_by_uri(self, subtopic, measure):
        try:
            return DbPage.query.filter_by(parent_guid=subtopic, uri=measure).one()
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


page_service = PageService()

import json
import os
import subprocess
import tempfile

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from application import db
from application.cms.exceptions import (
    UploadCheckError,
    UploadCheckPending,
    UploadCheckFailed,
    PageUnEditable,
    UploadNotFoundException,
    UploadAlreadyExists
)
from application.cms.models import Upload
from application.cms.service import Service
from application.utils import create_guid


class UploadService(Service):

    def __init__(self):
        super().__init__()

    def get_url_for_file(self, page, file_name, directory='data'):
        page_file_system = self.app.file_service.page_system(page)
        return page_file_system.url_for_file('%s/%s' % (directory, file_name))

    def copy_uploads(self, page, old_version):
        page_file_system = self.app.file_service.page_system(page)
        from_key = '%s/%s/source' % (page.guid, old_version)
        to_key = '%s/%s/source' % (page.guid, page.version)
        for upload in page.uploads:
            from_path = '%s/%s' % (from_key, upload.file_name)
            to_path = '%s/%s' % (to_key, upload.file_name)
            page_file_system.copy_file(from_path, to_path)

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

    def delete_upload_files(self, page, file_name):
        try:
            page_file_system = self.app.file_service.page_system(page)
            page_file_system.delete('source/%s' % file_name)
        except FileNotFoundError:
            self.logger.exception('Could not find source/%s' % file_name)

    def get_page_uploads(self, page):
        page_file_system = self.app.file_service.page_system(page)
        return page_file_system.list_files('data')

    def get_measure_download(self, upload, file_name, directory):
        page_file_system = self.app.file_service.page_system(upload.page)
        output_file = tempfile.NamedTemporaryFile(delete=False)
        key = '%s/%s' % (directory, file_name)
        page_file_system.read(key, output_file.name)
        return output_file.name

    def upload_data(self, page, file, filename=None):
        page_file_system = self.app.file_service.page_system(page)
        if not filename:
            filename = file.name
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file = '%s/%s' % (tmpdirname, filename)
            file.save(tmp_file)
            self.validate_file(tmp_file)
            if self.app.config['ATTACHMENT_SCANNER_ENABLED']:
                attachment_scanner_url = self.app.config['ATTACHMENT_SCANNER_API_URL']
                attachment_scanner_key = self.app.config['ATTACHMENT_SCANNER_API_KEY']
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

    def delete_upload_obj(self, page, upload):
        if page.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
            self.logger.error(message)
            raise PageUnEditable(message)
        try:
            self.delete_upload_files(page=page, file_name=upload.file_name)
        except FileNotFoundError:
            pass

        db.session.delete(upload)
        db.session.commit()

    def get_upload(self, page, file_name):
        try:
            upload = Upload.query.filter_by(page=page, file_name=file_name).one()
            return upload
        except NoResultFound as e:
            self.logger.exception(e)
            raise UploadNotFoundException()

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

        guid = create_guid(file_name)

        if not self.check_upload_title_unique(page, title):
            raise UploadAlreadyExists('An upload with that title already exists for this measure')
        else:
            self.logger.info('Upload with guid %s does not exist ok to proceed', guid)
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            self.upload_data(page, upload, filename=file_name)
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

    def create_upload_with_data(self, page, upload_data, title, description):
        import csv

        with tempfile.TemporaryDirectory() as tmpdirname:
            file_name = "%s.%s" % (slugify(title), 'csv')
            tmp_file_name = '%s/%s' % (tmpdirname, file_name)

            with open(tmp_file_name, 'w') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writerows(upload_data)

            if page.not_editable():
                message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(page.guid)
                self.logger.error(message)
                raise PageUnEditable(message)

            guid = create_guid(file_name)

            if not self.check_upload_title_unique(page, title):
                raise UploadAlreadyExists('An upload with that title already exists for this measure')
            else:
                self.upload_data_from_data_upload(page, tmp_file_name, file_name)

                db_upload = Upload(guid=guid,
                                   title=title,
                                   file_name=file_name,
                                   description=description,
                                   page=page,
                                   size="100kb")

                page.uploads.append(db_upload)
                db.session.add(page)
                db.session.commit()

            return db_upload

    def upload_data_from_data_upload(self, page, tmp_file, filename):
        page_file_system = self.app.file_service.page_system(page)
        page_file_system.write(tmp_file, 'source/%s' % secure_filename(filename))
        return page_file_system

    def edit_upload(self, measure, upload, data, file=None):
        if measure.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure.guid)
            self.logger.error(message)
            raise PageUnEditable(message)

        page_file_system = self.app.file_service.page_system(measure)

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
                upload_service.upload_data(measure, file, filename=file_name)
                if upload.file_name != file_name:
                    upload_service.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file_name
            else:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                file.size = size
                upload_service.upload_data(measure, file, filename=file.filename)
                if upload.file_name != file.filename:
                    upload_service.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file.filename
        else:
            if new_title != existing_title:  # current file needs renaming
                extension = upload.file_name.split('.')[-1]
                file_name = "%s.%s" % (slugify(data['title']), extension)
                if self.app.config.get('FILE_SERVICE', 'local').lower() == 'local':
                    path = self.get_url_for_file(measure, upload.file_name)
                    dir_path = os.path.dirname(path)
                    page_file_system.rename_file(upload.file_name, file_name, dir_path)
                else:
                    if data['title'] != upload.title:
                        path = '%s/%s/source' % (measure.guid, measure.version)
                        page_file_system.rename_file(upload.file_name, file_name, path)
                upload_service.delete_upload_files(page=measure, file_name=upload.file_name)
                upload.file_name = file_name

        upload.description = data['description'] if 'description' in data else upload.title
        upload.title = new_title

        db.session.add(upload)
        db.session.commit()

    @staticmethod
    def check_upload_title_unique(page, title):
        try:
            Upload.query.filter_by(page=page, title=title).one()
            return False
        except NoResultFound as e:
            return True


upload_service = UploadService()

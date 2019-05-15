import os
import tempfile

from slugify import slugify
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from application import db

from application.cms.exceptions import (
    PageUnEditable,
    UploadCheckError,
    UploadCheckPending,
    UploadError,
    UploadNotFoundException,
    UploadAlreadyExists,
)
from application.cms.models import Upload
from application.cms.scanner_service import scanner_service
from application.cms.service import Service
from application.utils import create_guid


class UploadService(Service):
    def __init__(self):
        super().__init__()

    def get_url_for_file(self, measure_version, file_name, directory="data"):
        page_file_system = self.app.file_service.page_system(measure_version)
        return page_file_system.url_for_file("%s/%s" % (directory, file_name))

    def copy_uploads_between_measure_versions(self, from_measure_version, to_measure_version):
        page_file_system = self.app.file_service.page_system(to_measure_version)
        from_key = "%s/%s/source" % (from_measure_version.measure.id, from_measure_version.version)
        to_key = "%s/%s/source" % (to_measure_version.measure.id, to_measure_version.version)

        for upload in to_measure_version.uploads:
            from_path = "%s/%s" % (from_key, upload.file_name)
            to_path = "%s/%s" % (to_key, upload.file_name)
            page_file_system.copy_file(from_path, to_path)

    def validate_file(self, filename):
        from chardet.universaldetector import UniversalDetector

        detector = UniversalDetector()
        detector.reset()

        with open(filename, "rb") as to_convert:
            for line in to_convert:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            encoding = detector.result.get("encoding")
        valid_encodings = ["ASCII", "ISO-8859-1", "UTF-8", "UTF-8-SIG"]

        if encoding is None:
            message = "Please check that you are uploading a CSV file."
            self.logger.exception(message)
            raise UploadCheckError(message)

        if encoding.upper() not in valid_encodings:
            message = "File encoding %s not valid. Valid encodings: %s" % (encoding, ", ".join(valid_encodings))
            self.logger.exception(message)
            raise UploadCheckError(message)

        return encoding.upper()

    def delete_upload_files(self, measure_version, file_name):
        try:
            page_file_system = self.app.file_service.page_system(measure_version)
            page_file_system.delete("source/%s" % file_name)
        except FileNotFoundError:
            self.logger.exception("Could not find source/%s" % file_name)

    def get_page_uploads(self, measure_version):
        page_file_system = self.app.file_service.page_system(measure_version)
        return page_file_system.list_files("data")

    def get_measure_download(self, upload, file_name, directory):
        page_file_system = self.app.file_service.page_system(upload.measure_version)
        output_file = tempfile.NamedTemporaryFile(delete=False)
        key = "%s/%s" % (directory, file_name)
        page_file_system.read(key, output_file.name)
        return output_file.name

    def upload_data(self, measure_version, file, filename=None):
        page_file_system = self.app.file_service.page_system(measure_version)
        if not filename:
            filename = file.name

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file = "%s/%s" % (tmpdirname, filename)
            file.save(tmp_file)
            self.validate_file(tmp_file)

            try:
                scanner_service.scan_file(filename=tmp_file, fileobj=open(tmp_file, "rb"))

            except UploadCheckPending:
                pass

            except UploadError:
                raise

            page_file_system.write(tmp_file, "source/%s" % secure_filename(filename))

        return page_file_system

    def delete_upload_obj(self, measure_version, upload):
        if measure_version.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(
                measure_version.title
            )
            self.logger.error(message)
            raise PageUnEditable(message)
        try:
            self.delete_upload_files(measure_version=measure_version, file_name=upload.file_name)
        except FileNotFoundError:
            pass

        db.session.delete(upload)
        db.session.commit()

    def get_upload(self, measure_version, file_name):
        try:
            upload = Upload.query.filter_by(measure_version=measure_version, file_name=file_name).one()
            return upload
        except NoResultFound as e:
            self.logger.exception(e)
            raise UploadNotFoundException()

    def create_upload(self, measure_version, upload, title, description):
        extension = upload.filename.split(".")[-1]
        if title and extension:
            file_name = "%s.%s" % (slugify(title), extension)
        else:
            file_name = upload.filename

        if measure_version.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(
                measure_version.title
            )
            self.logger.error(message)
            raise PageUnEditable(message)

        guid = create_guid(file_name)

        if not self.check_upload_title_unique(measure_version, title):
            raise UploadAlreadyExists("An upload with that title already exists for this measure")
        else:
            self.logger.info("Upload with guid %s does not exist ok to proceed", guid)
            upload.seek(0, os.SEEK_END)
            size = upload.tell()
            upload.seek(0)
            self.upload_data(measure_version, upload, filename=file_name)
            db_upload = Upload(
                guid=guid,
                title=title,
                file_name=file_name,
                description=description,
                measure_version=measure_version,
                size=size,
            )

            measure_version.uploads.append(db_upload)
            db.session.commit()

        return db_upload

    def edit_upload(self, measure_version, upload, data, file=None):
        if measure_version.not_editable():
            message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(
                measure_version.title
            )
            self.logger.error(message)
            raise PageUnEditable(message)

        page_file_system = self.app.file_service.page_system(measure_version)

        new_title = data.get("title", upload.title)
        existing_title = upload.title

        if file:
            if new_title:
                extension = file.filename.split(".")[-1]
                file_name = "%s.%s" % (slugify(data["title"]), extension)
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                file.size = size
                upload_service.upload_data(measure_version, file, filename=file_name)
                if upload.file_name != file_name:
                    upload_service.delete_upload_files(measure_version=measure_version, file_name=upload.file_name)
                upload.file_name = file_name
            else:
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                file.size = size
                upload_service.upload_data(measure_version, file, filename=file.filename)
                if upload.file_name != file.filename:
                    upload_service.delete_upload_files(measure_version=measure_version, file_name=upload.file_name)
                upload.file_name = file.filename
        else:
            if new_title != existing_title:  # current file needs renaming
                extension = upload.file_name.split(".")[-1]
                file_name = "%s.%s" % (slugify(data["title"]), extension)
                if self.app.config.get("FILE_SERVICE", "local").lower() == "local":
                    path = self.get_url_for_file(measure_version, upload.file_name)
                    dir_path = os.path.dirname(path)
                    page_file_system.rename_file(upload.file_name, file_name, dir_path)
                else:
                    if data["title"] != upload.title:
                        path = "%s/%s/source" % (measure_version.measure.id, measure_version.version)
                        page_file_system.rename_file(upload.file_name, file_name, path)
                upload_service.delete_upload_files(measure_version=measure_version, file_name=upload.file_name)
                upload.file_name = file_name

        upload.description = data["description"] if "description" in data else upload.title
        upload.title = new_title

        db.session.commit()

    @staticmethod
    def check_upload_title_unique(measure_version, title):
        try:
            Upload.query.filter_by(measure_version=measure_version, title=title).one()
            return False
        except NoResultFound:
            return True


upload_service = UploadService()

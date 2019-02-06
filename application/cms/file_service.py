import codecs
import os
import shutil
import boto3
import boto3.session
import mimetypes

from os import listdir
from os.path import isfile, join

import logging

from application.cms.exceptions import UploadCheckError
from application.utils import setup_module_logging

logger = logging.Logger(__name__)


class FileService:
    def __init__(self):
        self.system = None
        self.cache = None
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config["LOG_LEVEL"])
        service_type = app.config["FILE_SERVICE"]
        if service_type.lower() == "s3":
            self.system = S3FileSystem(bucket_name=app.config["S3_UPLOAD_BUCKET_NAME"], region=app.config["S3_REGION"])
            message = "Initialised S3 file system %s in %s" % (
                app.config["S3_UPLOAD_BUCKET_NAME"],
                app.config["S3_REGION"],
            )
            self.logger.info(message)
        elif service_type.lower() == "local":
            self.system = LocalFileSystem(root=app.config["LOCAL_ROOT"])
            self.logger.info("initialised local file system in %s" % (app.config["LOCAL_ROOT"]))

    def page_system(self, page):
        full_path = "%s/%s" % (page.guid, page.version)
        return PageFileSystem(self.system, full_path)


class PageFileSystem:
    def __init__(self, file_system, page_identifier):
        self.file_system = file_system
        self.page_identifier = page_identifier

    def read(self, fs_path, local_path):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        self.file_system.read(full_path, local_path)

    def write(self, local_path, fs_path):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        self.file_system.write(local_path, full_path)

    def list_paths(self, fs_path):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        return self.file_system.list_paths(full_path)

    def list_files(self, fs_path):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        return self.file_system.list_files(full_path)

    def delete(self, fs_path):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        self.file_system.delete(full_path)

    def url_for_file(self, fs_path, time_out=100):
        full_path = "%s/%s" % (self.page_identifier, fs_path)
        return self.file_system.url_for_file(full_path, time_out)

    def rename_file(self, key, new_key, fs_path):
        self.file_system.rename_file(key, new_key, fs_path)

    def copy_file(self, from_path, to_path):
        self.file_system.copy_file(from_path, to_path)


class S3FileSystem:
    """
    S3FileSystem requires two env variables to be stored for boto3 to initialise
    AWS_ACCESS_KEY_ID = xxxxxxxxxxxx
    AWS_SECRET_ACCESS_KEY = xxxxxxxxxxxxxxxxxxxx
    """

    def __init__(self, bucket_name, region):
        self.s3 = boto3.resource("s3")
        self.bucket = self.s3.Bucket(bucket_name)
        self.region = region
        self.bucket_name = bucket_name

    def read(self, fs_path, local_path):
        obj = self.s3.Object(self.bucket_name, fs_path)
        try:
            content = obj.get()["Body"].read().decode("utf-8")
            with codecs.open(local_path, "w", encoding="utf-8") as file:
                file.write(content)
            return local_path
        except UnicodeDecodeError:
            print("Could not decode %s using %s" % (fs_path, "utf-8, trying iso-8859-1"))
            content = obj.get()["Body"].read().decode("iso-8859-1")
            with codecs.open(local_path, "w", encoding="iso-8859-1") as file:
                file.write(content)
            return local_path
        except Exception as e:
            print("Could not decode %s using %s" % (fs_path, "utf-8 or iso-8859-1"))
            raise e

    def write(self, local_path, fs_path, max_age_seconds=300, strict=True):

        with open(file=local_path, mode="rb") as file:
            mimetype = mimetypes.guess_type(local_path, strict=False)[0]
            if mimetype is None and local_path.endswith(".map"):
                # .map files are sourcemaps which tell browsers how minified CSS and JS relates back to source files
                # setting mimetype to "application/json" is recommended and makes the files viewable in browsers
                mimetype = "application/json"
            if mimetype:
                self.bucket.upload_fileobj(
                    Key=fs_path,
                    Fileobj=file,
                    ExtraArgs={"ContentType": mimetype, "CacheControl": "max-age=%s" % max_age_seconds},
                )
            else:
                if strict:
                    raise UploadCheckError("Couldn't determine the type of file you uploaded")
                else:
                    logger.warning(f"Not writing file {fs_path} due to unknown mimetype.")

    def list_paths(self, fs_path):
        return [x.key for x in self.bucket.objects.filter(Prefix=fs_path)]

    def list_files(self, fs_path):
        return [x.key[len(fs_path) + 1 :] for x in self.bucket.objects.filter(Prefix=fs_path)]

    def delete(self, fs_path):
        self.bucket.delete_objects(Delete={"Objects": [{"Key": fs_path}]})

    def url_for_file(self, fs_path, time_out=100):
        session = boto3.session.Session(region_name=self.region)
        s3_client = session.client("s3", config=boto3.session.Config(signature_version="s3v4"))

        presigned_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket.name, "Key": fs_path}, ExpiresIn=time_out
        )
        return presigned_url

    def rename_file(self, key, new_key, fs_path):
        self.s3.Object(self.bucket_name, "%s/%s" % (fs_path, new_key)).copy_from(
            CopySource="%s/%s/%s" % (self.bucket_name, fs_path, key)
        )

    def copy_file(self, from_path, to_path):
        self.s3.Object(self.bucket_name, to_path).copy_from(CopySource="%s/%s" % (self.bucket_name, from_path))


class LocalFileSystem:
    def __init__(self, root):
        self.root = root

    def read(self, fs_path, local_path):
        # TODO - Did I notice some safe version of this?
        full_path = "%s/%s" % (self.root, fs_path)
        shutil.copyfile(full_path, local_path)

    def write(self, local_path, fs_path):
        full_path = "%s/%s" % (self.root, fs_path)

        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        shutil.copyfile(local_path, full_path)

    def list_paths(self, fs_path):
        full_path = "%s/%s" % (self.root, fs_path)
        try:
            return ["%s/%s" % (full_path, f) for f in listdir(full_path) if isfile(join(full_path, f))]
        except FileNotFoundError:
            return []

    def list_files(self, fs_path):
        full_path = "%s/%s" % (self.root, fs_path)
        try:
            return [f for f in listdir(full_path) if isfile(join(full_path, f))]
        except FileNotFoundError:
            return []

    def delete(self, fs_path):
        full_path = "%s/%s" % (self.root, fs_path)
        os.remove(path=full_path)

    def url_for_file(self, fs_path, time_out=100):
        return "%s/%s" % (self.root, fs_path)

    def rename_file(self, key, new_key, fs_path):
        os.rename("%s/%s" % (fs_path, key), "%s/%s" % (fs_path, new_key))
        fs_path = fs_path.replace("data", "source")
        os.rename("%s/%s" % (fs_path, key), "%s/%s" % (fs_path, new_key))

    def copy_file(self, from_path, to_path):
        pass

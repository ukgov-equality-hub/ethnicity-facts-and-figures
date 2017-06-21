import boto3
import shutil
import os
import tempfile
from os import listdir
from os.path import isfile, join

from application.cms.models import Page


class FileService:

    def __init__(self):
        self.system = None

    def init_app(self, app):
        try:
            service_type = app.config['FILE_SERVICE']
            if service_type in ['S3', 's3']:
                self.system = S3FileSystem(bucket_name=app.config['S3_BUCKET_NAME'])
            elif service_type in ['Local', 'LOCAL']:
                self.system = LocalFileSystem(root=app.config['LOCAL_ROOT'])
            else:
                self.system = TemporaryFileSystem()
        except KeyError:
            self.system = TemporaryFileSystem()


class S3FileSystem:
    """
    S3FileSystem requires two env variables to be stored for boto3 to initialise
    AWS_ACCESS_KEY_ID = xxxxxxxxxxxx
    AWS_SECRET_ACCESS_KEY = xxxxxxxxxxxxxxxxxxxx
    """
    def __init__(self, bucket_name):
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(bucket_name)

    def read(self, fs_path, local_path):

        with open(file=local_path, mode='wb') as file:
            self.bucket.download_fileobj(Key=fs_path, Fileobj=file)

    def write(self, local_path, fs_path):

        with open(file=local_path, mode='rb') as file:
            self.bucket.upload_fileobj(Key=fs_path, Fileobj=file)

    def list_paths(self, fs_path):
        return [x.key for x in self.bucket.objects.filter(Prefix=fs_path)]

    def list_files(self, fs_path):
        return [x.key[len(fs_path) + 1:] for x in self.bucket.objects.filter(Prefix=fs_path)]

    def delete(self, fs_path):
        self.bucket.delete_objects(Delete={'Objects': [{'Key': fs_path}]})


class LocalFileSystem:

    def __init__(self, root):
        self.root = root

    def read(self, fs_path, local_path):
        # TODO - Did I notice some safe version of this?
        full_path = '%s/%s' % (self.root, fs_path)
        shutil.copyfile(full_path, local_path)

    def write(self, local_path, fs_path):
        full_path = '%s/%s' % (self.root, fs_path)

        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))

        shutil.copyfile(local_path, full_path)

    def list_paths(self, fs_path):
        full_path = '%s/%s' % (self.root, fs_path)
        return ['%s/%s' % (full_path, f) for f in listdir(full_path) if isfile(join(full_path, f))]

    def list_files(self, fs_path):
        full_path = '%s/%s' % (self.root, fs_path)
        return [f for f in listdir(full_path) if isfile(join(full_path, f))]

    def delete(self, fs_path):
        full_path = '%s/%s' % (self.root, fs_path)
        os.remove(path=full_path)


class TemporaryFileSystem(LocalFileSystem):

    def __init__(self):
        self.folder = tempfile.mkdtemp()
        super().__init__(root=self.folder)


file_service = FileService()

import ast
import os
import logging
from os.path import join, dirname
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break. For CI env variables are set in circle.yml
# In Heroku, well... they are set in Heroku.

from application.utils import get_bool

p = Path(dirname(__file__))
dotenv_path = join(str(p.parent), '.env')
load_dotenv(dotenv_path)


class Config:
    DEBUG = False
    LOG_LEVEL = logging.INFO
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'PROD')
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))
    WTF_CSRF_ENABLED = True

    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    HTML_CONTENT_REPO = 'rd_html'
    RDU_GITHUB_URL = os.environ.get('RDU_GITHUB_URL', 'github.com/methods')
    RDU_GITHUB_ACCESS_TOKEN = os.environ.get('RDU_GITHUB_ACCESS_TOKEN', GITHUB_ACCESS_TOKEN)
    STATIC_SITE_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(RDU_GITHUB_ACCESS_TOKEN,
                                                                       '/'.join((RDU_GITHUB_URL,
                                                                                HTML_CONTENT_REPO)))

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('PERMANENT_SESSION_LIFETIME_MINS', 60)))
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_URL_PREFIX = '/auth'

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # might be useful at some point
    RESEARCH = get_bool(os.environ.get('RESEARCH', False))

    if RESEARCH:
        SECURITY_POST_LOGIN_VIEW = '/prototype'

    SECURITY_FLASH_MESSAGES = False
    BUILD_DIR = os.environ['BUILD_DIR']
    BETA_PUBLICATION_STATES = ast.literal_eval(os.environ.get('BETA_PUBLICATION_STATES', "['ACCEPTED']"))

    FILE_SERVICE = os.environ.get('FILE_SERVICE', 'Temporary')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
    S3_REGION = os.environ.get('S3_REGION', 'eu-west-2')

    HARMONISER_ENABLED = get_bool(os.environ.get('HARMONISER_ENABLED', False))
    HARMONISER_FILE = 'application/data/ethnicity_lookup.csv'

    SIMPLE_CHART_BUILDER = get_bool(os.environ.get('SIMPLE_CHART_BUILDER', False))
    RDU_SITE = os.environ.get('RDU_SITE', 'https://ethnicity-facts-and-figures.herokuapp.com')


class DevConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    PUSH_ENABLED = False
    FETCH_ENABLED = False
    WTF_CSRF_ENABLED = False
    ENVIRONMENT = 'DEV'


class TestConfig(DevConfig):
    if os.environ['ENVIRONMENT'] == 'CI':
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/rdcms_test')
    LOGIN_DISABLED = False
    WORK_WITH_REMOTE = False
    FILE_SERVICE = 'Temporary'

    HARMONISER_ENABLED = True
    HARMONISER_FILE = 'tests/test_data/test_lookups/test_lookup.csv'


class EmptyConfig(TestConfig):

    def __init__(self, repo_dir):
        self.REPO_DIR = repo_dir

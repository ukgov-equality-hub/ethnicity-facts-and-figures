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
    SESSION_COOKIE_SECURE = True

    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    HTML_CONTENT_REPO = os.environ.get('HTML_CONTENT_REPO', 'rd_html')
    GITHUB_URL = os.environ.get('GITHUB_URL', 'github.com/methods')
    STATIC_SITE_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(GITHUB_ACCESS_TOKEN,
                                                                       '/'.join((GITHUB_URL,
                                                                                HTML_CONTENT_REPO)))

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('PERMANENT_SESSION_LIFETIME_MINS', 360)))
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_URL_PREFIX = '/auth'
    SECURITY_EMAIL_SENDER = 'noreply@ethnicity-facts-figures.service.gov.uk'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESEARCH = get_bool(os.environ.get('RESEARCH', False))

    SECURITY_FLASH_MESSAGES = False
    STATIC_BUILD_DIR = os.environ['STATIC_BUILD_DIR']

    FILE_SERVICE = os.environ.get('FILE_SERVICE', 'Local')

    S3_UPLOAD_BUCKET_NAME = os.environ['S3_UPLOAD_BUCKET_NAME']
    S3_STATIC_SITE_BUCKET = os.environ['S3_STATIC_SITE_BUCKET']
    S3_REGION = os.environ.get('S3_REGION', 'eu-west-2')
    LOCAL_ROOT = os.environ.get('LOCAL_ROOT', None)
    HARMONISER_FILE = os.environ.get('HARMONISER_FILE', './application/data/ethnicity_lookup.csv')
    HARMONISER_DEFAULTS = ['*', '*', 'Unclassified', 960]
    SIMPLE_CHART_BUILDER = get_bool(os.environ.get('SIMPLE_CHART_BUILDER', False))
    RDU_SITE = os.environ.get('RDU_SITE', 'https://www.ethnicity-facts-figures.service.gov.uk')
    RDU_EMAIL = os.environ.get('RDU_EMAIL', 'ethnicity@cabinetoffice.gov.uk')

    LOCAL_BUILD = get_bool(os.environ.get('LOCAL_BUILD', False))

    BUILD_SITE = get_bool(os.environ.get('BUILD_SITE', False))
    PUSH_SITE = get_bool(os.environ.get('PUSH_SITE', False))
    DEPLOY_SITE = get_bool(os.environ.get('DEPLOY_SITE', False))

    ATTACHMENT_SCANNER_ENABLED = get_bool(os.environ.get('ATTACHMENT_SCANNER_ENABLED', False))
    ATTACHMENT_SCANNER_API_URL = os.environ.get('ATTACHMENT_SCANNER_API_URL', '')
    ATTACHMENT_SCANNER_API_KEY = os.environ.get('ATTACHMENT_SCANNER_API_KEY', '')

    JSON_ENABLED = get_bool(os.environ.get('JSON_ENABLED', False))

    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

    MAIL_SERVER = os.environ.get('MAILGUN_SMTP_SERVER')
    MAIL_USE_SSL = True
    MAIL_PORT = int(os.environ.get('MAILGUN_SMTP_PORT', 465))
    MAIL_USERNAME = os.environ.get('MAILGUN_SMTP_LOGIN')
    MAIL_PASSWORD = os.environ.get('MAILGUN_SMTP_PASSWORD')
    TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24
    PREVIEW_TOKEN_MAX_AGE_DAYS = int(os.environ.get('PREVIEW_TOKEN_MAX_AGE_DAYS', 14))
    SURVEY_ENABLED = get_bool(os.environ.get('SURVEY_ENABLED', False))
    WTF_CSRF_TIME_LIMIT = None


class DevConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    PUSH_ENABLED = False
    FETCH_ENABLED = False
    ENVIRONMENT = 'DEV'
    SESSION_COOKIE_SECURE = False
    SERVER_NAME = 'localhost:5000'


class TestConfig(DevConfig):
    if os.environ.get('ENVIRONMENT', "CI") == 'CI':
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/rdcms_test')
    LOGIN_DISABLED = False
    WORK_WITH_REMOTE = False
    FILE_SERVICE = 'Local'
    HARMONISER_FILE = 'tests/test_data/test_lookups/test_lookup.csv'
    HARMONISER_DEFAULTS = ['*', '*', 'Unclassified', 960]
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    ATTACHMENT_SCANNER_ENABLED = False

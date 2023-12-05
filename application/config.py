import logging
import os
from datetime import timedelta
from dotenv import load_dotenv
from os.path import join, dirname
from pathlib import Path

from application.utils import get_bool

# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break.
# CI env variables are set in Heroku.

app_base_path = Path(dirname(__file__))
dotenv_path = join(str(app_base_path.parent), ".env")
load_dotenv(dotenv_path)


class Config:
    DEBUG = False
    LOG_LEVEL = logging.getLevelName(os.environ["LOG_LEVEL"]) if "LOG_LEVEL" in os.environ else logging.INFO
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "PRODUCTION")
    SECRET_KEY = os.environ["SECRET_KEY"]
    PROJECT_NAME = "ethnicity-facts-and-figures-publisher"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    STATIC_MODE = False

    GITHUB_ACCESS_TOKEN = os.environ["GITHUB_ACCESS_TOKEN"]
    GITHUB_URL = os.environ.get("GITHUB_URL", "github.com/racedisparityaudit")
    STATIC_SITE_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(
        GITHUB_ACCESS_TOKEN, "/".join((GITHUB_URL, HTML_CONTENT_REPO))
    )

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get("PERMANENT_SESSION_LIFETIME_MINS", 360)))
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_URL_PREFIX = "/auth"
    SECURITY_EMAIL_SENDER = "noreply@ethnicity-facts-figures.service.gov.uk"
    SECURITY_TRACKABLE = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESEARCH = get_bool(os.environ.get("RESEARCH", False))

    SECURITY_FLASH_MESSAGES = False
    STATIC_BUILD_DIR = os.environ["STATIC_BUILD_DIR"]

    FILE_SERVICE = os.environ.get("FILE_SERVICE", "Local")

    S3_UPLOAD_BUCKET_NAME = os.environ["S3_UPLOAD_BUCKET_NAME"]
    S3_STATIC_SITE_BUCKET = os.environ["S3_STATIC_SITE_BUCKET"]
    S3_STATIC_SITE_ERROR_PAGES_BUCKET = os.environ["S3_STATIC_SITE_ERROR_PAGES_BUCKET"]
    S3_REGION = os.environ.get("S3_REGION", "eu-west-2")
    LOCAL_ROOT = os.environ.get("LOCAL_ROOT", None)

    ETHNICITY_CLASSIFICATION_FINDER_LOOKUP = os.environ.get(
        "CLASSIFICATION_FINDER_LOOKUP", "./application/data/static/standardisers/classification_lookup.csv"
    )
    ETHNICITY_CLASSIFICATION_FINDER_CLASSIFICATIONS = os.environ.get(
        "ETHNICITY_CLASSIFICATION_FINDER_CLASSIFICATIONS",
        "./application/data/static/standardisers/classification_definitions.csv",
    )

    SIMPLE_CHART_BUILDER = get_bool(os.environ.get("SIMPLE_CHART_BUILDER", False))
    RDU_SITE = os.environ.get("RDU_SITE", "https://www.ethnicity-facts-figures.service.gov.uk")
    RDU_EMAIL = os.environ.get("RDU_EMAIL", "noreply@ethnicity-facts-figures.service.gov.uk")

    LOCAL_BUILD = get_bool(os.environ.get("LOCAL_BUILD", False))

    BUILD_SITE = get_bool(os.environ.get("BUILD_SITE", False))
    PUSH_SITE = get_bool(os.environ.get("PUSH_SITE", False))
    DEPLOY_SITE = get_bool(os.environ.get("DEPLOY_SITE", False))

    ATTACHMENT_SCANNER_ENABLED = get_bool(os.environ.get("ATTACHMENT_SCANNER_ENABLED", False))
    ATTACHMENT_SCANNER_URL = os.environ.get("ATTACHMENT_SCANNER_URL", "")
    ATTACHMENT_SCANNER_API_TOKEN = os.environ.get("ATTACHMENT_SCANNER_API_TOKEN", "")

    GOOGLE_ANALYTICS_ID = os.environ["GOOGLE_ANALYTICS_ID"]

    NOTIFY_API = os.environ.get("NOTIFY_API", "")
    TOKEN_MAX_AGE_SECONDS = 60 * 60 * 48
    PREVIEW_TOKEN_MAX_AGE_DAYS = int(os.environ.get("PREVIEW_TOKEN_MAX_AGE_DAYS", 14))
    SURVEY_ENABLED = get_bool(os.environ.get("SURVEY_ENABLED", False))
    WTF_CSRF_TIME_LIMIT = None

    TRELLO_API_KEY = os.environ.get("TRELLO_API_KEY", "")
    TRELLO_API_TOKEN = os.environ.get("TRELLO_API_TOKEN", "")

    GOOGLE_CUSTOM_SEARCH_ENDPOINT = "https://cse.google.com/cse/publicurl"
    GOOGLE_CUSTOM_SEARCH_ID = "018356501072542209775:85_lddxwwh4"

    REDIRECT_HTTP_CODE = os.environ.get("REDIRECT_HTTP_CODE", 301)
    REDIRECT_PROTOCOL = os.environ.get("REDIRECT_PROTOCOL", "http")
    REDIRECT_HOSTNAME = os.environ.get("REDIRECT_HOSTNAME", "localhost")

    NEWSLETTER_SUBSCRIBE_URL = os.environ.get("NEWSLETTER_SUBSCRIBE_URL", "").replace('__AND__', '&')


class DevConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.getLevelName(os.environ["LOG_LEVEL"]) if "LOG_LEVEL" in os.environ else logging.DEBUG
    ENVIRONMENT = "DEVELOPMENT"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_DOMAIN = False
    SERVER_NAME = "localhost:5000"
    # When testing IE using vm replace SERVER_NAME with 10.0.2.2:5000


class TestConfig(DevConfig):
    if os.environ.get("ENVIRONMENT", "CI") == "CI":
        SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/rdcms_test")
    LOGIN_DISABLED = False
    WORK_WITH_REMOTE = False
    FILE_SERVICE = "Local"

    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    ATTACHMENT_SCANNER_ENABLED = False
    ATTACHMENT_SCANNER_API_TOKEN = "fakeToken"
    ATTACHMENT_SCANNER_URL = "http://scanner-service"

    # Prevent exception reporting under test as `AssertionError: Popped wrong request context.`
    # While some report this don't work, it does seem to work for us.
    # https://github.com/jarus/flask-testing/issues/21
    PRESERVE_CONTEXT_ON_EXCEPTION = False

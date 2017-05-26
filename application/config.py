import os
from os.path import join, dirname
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break. For CI env variables are set in circle.yml
# In Heroku, well... they are set in Heroku.
from flask import json

p = Path(dirname(__file__))
dotenv_path = join(str(p.parent), '.env')
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))
    WTF_CSRF_ENABLED = True

    CONTENT_REPO = 'rd_content'  # Name of repo on github
    CONTENT_DIR = 'content'
    REPO_DIR = os.environ['REPO_DIR']
    REPO_BRANCH = os.environ['REPO_BRANCH']

    GITHUB_URL = 'github.com/methods'
    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    GITHUB_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(GITHUB_ACCESS_TOKEN,
                                                                  '/'.join((GITHUB_URL,
                                                                            CONTENT_REPO)))

    PUSH_ENABLED = bool(os.environ.get('PUSH_ENABLED', True))
    FETCH_ENABLED = bool(os.environ.get('FETCH_ENABLED', True))
    WORK_WITH_REMOTE = bool(os.environ.get('WORK_WITH_REMOTE', True))

    ENVIRONMENT = os.environ['ENVIRONMENT']
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_URL_PREFIX = '/auth'

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # might be useful at some point
    RESEARCH = os.environ.get('RESEARCH')

    if RESEARCH:
        SECURITY_POST_LOGIN_VIEW = '/prototype'

    SECURITY_FLASH_MESSAGES = False


class DevConfig(Config):
    DEBUG = True
    PUSH_ENABLED = False
    FETCH_ENABLED = False
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', False)


class TestConfig(DevConfig):
    if os.environ['ENVIRONMENT'] == 'CI':
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/rdcms_test')
    LOGIN_DISABLED = False
    WORK_WITH_REMOTE = False


class EmptyConfig(TestConfig):

    def __init__(self, repo_dir):
        self.REPO_DIR = repo_dir

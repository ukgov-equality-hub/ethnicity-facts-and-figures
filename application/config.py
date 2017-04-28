import os
from os.path import join, dirname
from pathlib import Path
from dotenv import load_dotenv

# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break. For CI env variables are set in circle.yml
# In Heroku, well... they are set in Heroku.
p = Path(dirname(__file__))
dotenv_path = join(str(p.parent), '.env')
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))
    WTF_CSRF_ENABLED = False

    CONTENT_REPO = 'rd_content'  # Name of repo on github
    CONTENT_DIR = 'content'
    REPO_DIR = os.environ['REPO_DIR']
    REPO_BRANCH = os.environ['REPO_BRANCH']

    GITHUB_URL = 'github.com/methods'
    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    GITHUB_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(GITHUB_ACCESS_TOKEN,
                                                                  '/'.join((GITHUB_URL,
                                                                            CONTENT_REPO)))

    PUSH_ENABLED = os.environ.get('PUSH_ENABLED', True)
    ENVIRONMENT = os.environ['ENVIRONMENT']


class DevConfig(Config):
    DEBUG = True
    PUSH_ENABLED = False


class TestConfig(DevConfig):
    TESTING = True

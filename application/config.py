import os
from os.path import join, dirname
from pathlib import Path
from dotenv import load_dotenv


# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break. For CI env variables are set in circle.yml
# In Heroku, well... they are set in Heroku.
p = Path(dirname(__file__))
dotenv_path = join(p.parent, '.env')
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))

    # Should point to content repo top level directory
    CONTENT_REPO = os.environ['RD_CONTENT_REPO']
    CONTENT_DIRECTORY = '/'.join((CONTENT_REPO, "content"))
    WTF_CSRF_ENABLED = False


class DevConfig(Config):
    DEBUG = True


class TestConfig(DevConfig):
    TESTING = True

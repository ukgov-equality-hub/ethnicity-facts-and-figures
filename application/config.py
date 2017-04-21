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


    GITHUB_URL = 'github.com/methods'
    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    CONTENT_REPO = 'rd_content'
    CONTENT_DIR = 'content'  # This is the top level directory for pages  in the content repo

    # The REPOS_DIRECTORY folder will contain several content repos, one for each branch, it is not a repo itself
    REPOS_DIRECTORY = os.environ['RD_CONTENT_REPOS']


class DevConfig(Config):
    DEBUG = True


class TestConfig(DevConfig):
    TESTING = True

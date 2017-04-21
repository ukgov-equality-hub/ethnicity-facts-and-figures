import os


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    GITHUB_URL = 'github.com/methods'
    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    CONTENT_REPO = 'rd_content'
    CONTENT_DIR = 'content'  # This is the top level directory for pages  in the content repo

    # The REPOS_DIRECTORY folder will contain several content repos, one for each branch, it is not a repo itself
    REPOS_DIRECTORY = os.environ['RD_CONTENT_REPOS']


class DevConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class TestConfig(DevConfig):
    TESTING = True
    SERVER_NAME = 'test'

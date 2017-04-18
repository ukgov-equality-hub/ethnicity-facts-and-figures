import os


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']


class DevConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class TestConfig(DevConfig):
    TESTING = True
    SERVER_NAME = 'test'
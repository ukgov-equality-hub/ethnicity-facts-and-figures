import os

if os.environ.get('SQREEN_TOKEN') is not None:
    import sqreen
    sqreen.start()

from application.config import Config
from application.factory import create_app

app = create_app(Config)

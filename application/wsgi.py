import os

from application.config import Config
from application.factory import create_app

if os.environ.get("SQREEN_TOKEN") is not None:
    import sqreen  # noqa

    sqreen.start()

app = create_app(Config)

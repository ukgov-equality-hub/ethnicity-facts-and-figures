from application.config import Config
from application.factory import create_app

app = create_app(Config)

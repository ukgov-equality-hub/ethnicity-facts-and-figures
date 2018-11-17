import inspect
import logging

from application.utils import setup_module_logging
from flask.app import Flask


class Service:
    def __init__(self) -> None:
        self.logger = logging.getLogger(inspect.getmodule(self).__name__)

    def init_app(self, app: Flask) -> None:
        self.logger = setup_module_logging(self.logger, app.config["LOG_LEVEL"])
        self.logger.info("Initialised %s", self.__class__.__name__)
        self.app = app

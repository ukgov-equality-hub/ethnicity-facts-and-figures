import inspect
import logging

from application.utils import setup_module_logging


class Service:

    def __init__(self):
        self.logger = logging.Logger(inspect.getmodule(self).__name__)

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised %s', self.__class__.__name__)
        self.app = app

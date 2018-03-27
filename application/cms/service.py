import logging

from application.utils import setup_module_logging


logger = logging.Logger(__name__)


class Service:

    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config['LOG_LEVEL'])
        self.logger.info('Initialised %s', self.__class__.__name__)
        self.app = app

from flask import Flask

from cms.views import cms

application = Flask(__name__)
application.register_blueprint(cms)
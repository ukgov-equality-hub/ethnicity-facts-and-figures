from flask import Flask
from application.auth import login_manager


def create_app(config_object):

    from application.auth import auth_blueprint
    from application.cms import cms_blueprint

    app = Flask(__name__)
    app.config.from_object(config_object)

    login_manager.init_app(app)

    app.register_blueprint(cms_blueprint)
    app.register_blueprint(auth_blueprint)

    return app

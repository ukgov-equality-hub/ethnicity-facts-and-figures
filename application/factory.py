from flask import (
    Flask,
    render_template
)

from application.auth import login_manager
from application.cms.filters import (
    format_page_guid,
    format_approve_button,
    format_as_title
)

from application.cms.page_service import page_service


def create_app(config_object):

    from application.auth import auth_blueprint
    from application.cms import cms_blueprint
    from application.preview import preview_blueprint

    app = Flask(__name__)
    app.config.from_object(config_object)

    login_manager.init_app(app)
    page_service.init_app(app)

    app.register_blueprint(cms_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(preview_blueprint)

    register_errorhandlers(app)
    app.after_request(harden_app)

    app.add_template_filter(format_page_guid)
    app.add_template_filter(format_approve_button)
    app.add_template_filter(format_as_title)

    return app


#  https://www.owasp.org/index.php/List_of_useful_HTTP_headers
def harden_app(response):
    response.headers.add('X-Frame-Options', 'deny')
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    # response.headers.add('Content-Security-Policy', (
    #     "default-src 'self' 'unsafe-inline';"
    #     "script-src 'self' 'unsafe-inline' 'unsafe-eval' data:;"
    #     "object-src 'self';"
    #     "font-src 'self' data:;"
    # ))
    # wait and see for the content security policy stuff
    return response


def register_errorhandlers(app):

    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template("error/{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        # add more codes if we create templates for them
        app.errorhandler(errcode)(render_error)
    return None

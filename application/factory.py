import os
import sys
import logging
import re

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    send_from_directory)
from flask_security import (
    SQLAlchemyUserDatastore,
    Security,
    current_user
)

from raven.contrib.flask import Sentry

from application import db
from application.auth.models import (
    User,
    Role
)

from application.cms.filters import (
    format_page_guid,
    format_approve_button,
    format_as_title,
    truncate_words,
    format_date_time,
    format_friendly_date,
    format_versions,
    format_status
)

from application.cms.file_service import FileService
from application.cms.page_service import page_service
from application.cms.data_utils import Harmoniser

from application.static_site.filters import (
    render_markdown,
    breadcrumb_friendly,
    filesize
)


def create_app(config_object):

    from application.static_site import static_site_blueprint
    from application.cms import cms_blueprint
    from application.audit import audit_blueprint

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.file_service = FileService()
    app.file_service.init_app(app)

    page_service.init_app(app)
    db.init_app(app)

    app.harmoniser = Harmoniser(config_object.HARMONISER_FILE)

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, user_datastore)

    if os.environ.get('SENTRY_DSN') is not None:
        sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

    app.register_blueprint(cms_blueprint)
    app.register_blueprint(audit_blueprint)
    app.register_blueprint(static_site_blueprint)

    # https://stackoverflow.com/questions/17135006/url-routing-conflicts-for-static-files-in-flask-dev-server
    if app.config.get('ENVIRONMENT', 'DEV').lower() == 'dev':
        @app.route('/static/<path:fullpath>')
        def static_subdir(fullpath):
            file_path = 'static/%s' % fullpath
            return send_from_directory('static', file_path)

    register_errorhandlers(app)
    app.after_request(harden_app)

    app.add_template_filter(format_page_guid)
    app.add_template_filter(format_approve_button)
    app.add_template_filter(format_as_title)
    app.add_template_filter(truncate_words)
    app.add_template_filter(format_date_time)
    app.add_template_filter(render_markdown)
    app.add_template_filter(breadcrumb_friendly)
    app.add_template_filter(filesize)
    app.add_template_filter(format_friendly_date)
    app.add_template_filter(format_versions)
    app.add_template_filter(format_status)

    # There is a CSS caching problem in chrome
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 10

    setup_app_logging(app, config_object)

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

        if re.match("/cms", request.path):
            return render_template("error/{0}.html".format(error_code)), error_code
        else:
            return render_template("static_site/error/{0}.html".format(error_code), asset_path="/static/"), error_code

    for errcode in [401, 403, 404, 500]:
        # add more codes if we create templates for them
        app.errorhandler(errcode)(render_error)
    return None


def setup_user_audit(app):
    from application.audit.auditor import record_login, record_logout
    from flask_login import user_logged_in, user_logged_out

    user_logged_in.connect(record_login, app)
    user_logged_out.connect(record_logout, app)


def setup_app_logging(app, config):
    context_provider = ContextualFilter()
    app.logger.addFilter(context_provider)
    log_format = '%(ip)s - [%(asctime)s] %(levelname)s "%(method)s %(url)s" - [user:%(user_id)s - %(message)s]'
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(config.LOG_LEVEL)


class ContextualFilter(logging.Filter):
    def filter(self, log_record):
        log_record.url = request.path
        log_record.method = request.method
        log_record.ip = request.environ.get("REMOTE_ADDR")
        log_record.user_id = -1 if current_user.is_anonymous else current_user.email
        return True

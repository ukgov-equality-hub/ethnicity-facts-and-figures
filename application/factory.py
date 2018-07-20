import os
import re
import sys
import logging

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory
)
from flask_security import (
    SQLAlchemyUserDatastore,
    Security,
    current_user
)
from raven.contrib.flask import Sentry

from application import db, mail
from application.auth.models import User
from application.cms.data_utils import Harmoniser, AutoDataGenerator
from application.cms.file_service import FileService
from application.cms.filters import (
    format_page_guid,
    format_approve_button,
    format_date_time,
    format_friendly_date,
    format_friendly_short_date,
    format_friendly_short_date_with_year,
    format_versions,
    format_status,
)
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.cms.dimension_service import dimension_service
from application.dashboard.trello_service import trello_service

from application.static_site.filters import (
    render_markdown,
    breadcrumb_friendly,
    filesize,
    value_filter,
    flatten,
    version_filter,
    flatten_chart,
    strip_trailing_slash,
    join_enum_display_names,
    slugify_value,
    first_bullet
)


def create_app(config_object):
    from application.static_site import static_site_blueprint
    from application.cms import cms_blueprint
    from application.admin import admin_blueprint
    from application.register import register_blueprint
    from application.auth import auth_blueprint
    from application.dashboard import dashboard_blueprint
    from application.review import review_blueprint

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.file_service = FileService()
    app.file_service.init_app(app)

    page_service.init_app(app)
    upload_service.init_app(app)
    dimension_service.init_app(app)

    trello_service.init_app(app)
    trello_service.set_credentials(config_object.TRELLO_API_KEY, config_object.TRELLO_API_TOKEN)

    db.init_app(app)

    app.harmoniser = Harmoniser(config_object.HARMONISER_FILE, default_values=config_object.HARMONISER_DEFAULTS)
    app.auto_data_generator = AutoDataGenerator.from_files(
        standardiser_file='application/data/builder/autodata_standardiser.csv',
        preset_file='application/data/builder/autodata_presets.csv')

    # Note not using Flask-Security role model
    user_datastore = SQLAlchemyUserDatastore(db, User, None)
    Security(app, user_datastore)

    if os.environ.get('SENTRY_DSN') is not None:
        sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

    app.register_blueprint(cms_blueprint)
    app.register_blueprint(static_site_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(register_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(review_blueprint)

    # To stop url clash between this and the measure page url (which is made of four variables.
    # See: https://stackoverflow.com/questions/17135006/url-routing-conflicts-for-static-files-in-flask-dev-server
    @app.route('/static/<path:subdir1>/<subdir2>/<file_name>')
    def static_subdir(subdir1, subdir2, file_name):
        file_path = "%s/%s/%s" % (subdir1, subdir2, file_name)
        return send_from_directory('static', file_path)

    register_errorhandlers(app)
    app.after_request(harden_app)

    # Render jinja templates with less whitespace; applies to both CMS and static build
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    app.add_template_filter(format_page_guid)
    app.add_template_filter(format_approve_button)
    app.add_template_filter(format_date_time)
    app.add_template_filter(render_markdown)
    app.add_template_filter(breadcrumb_friendly)
    app.add_template_filter(filesize)
    app.add_template_filter(format_friendly_date)
    app.add_template_filter(format_friendly_short_date)
    app.add_template_filter(format_friendly_short_date_with_year)
    app.add_template_filter(format_versions)
    app.add_template_filter(format_status)
    app.add_template_filter(value_filter)
    app.add_template_filter(flatten)
    app.add_template_filter(flatten_chart)
    app.add_template_filter(version_filter)
    app.add_template_filter(strip_trailing_slash)
    app.add_template_filter(join_enum_display_names)
    app.add_template_filter(slugify_value)
    app.add_template_filter(first_bullet)

    # There is a CSS caching problem in chrome
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 10

    setup_app_logging(app, config_object)

    if os.environ.get('SQREEN_TOKEN') is not None:
        setup_sqreen_audit(app)

    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    from flask_sslify import SSLify
    SSLify(app)

    mail.init_app(app)

    @app.context_processor
    def inject_globals():
        from application.auth.models import (
             CREATE_MEASURE,
             CREATE_VERSION,
             DELETE_MEASURE,
             MANAGE_SYSTEM,
             MANAGE_USERS,
             ORDER_MEASURES,
             PUBLISH,
             READ,
             UPDATE_MEASURE,
             VIEW_DASHBOARDS,
        )
        return dict(
            CREATE_MEASURE=CREATE_MEASURE,
            CREATE_VERSION=CREATE_VERSION,
            DELETE_MEASURE=DELETE_MEASURE,
            MANAGE_SYSTEM=MANAGE_SYSTEM,
            MANAGE_USERS=MANAGE_USERS,
            ORDER_MEASURES=ORDER_MEASURES,
            PUBLISH=PUBLISH,
            READ=READ,
            UPDATE_MEASURE=UPDATE_MEASURE,
            VIEW_DASHBOARDS=VIEW_DASHBOARDS,
        )

    return app


#  https://www.owasp.org/index.php/List_of_useful_HTTP_headers
def harden_app(response):
    response.headers.add('X-Frame-Options', 'deny')
    response.headers.add('X-Content-Type-Options', 'nosniff')
    response.headers.add('X-XSS-Protection', '1; mode=block')
    response.headers.add('Content-Security-Policy', (
        "default-src 'self';"
        "script-src 'self' 'unsafe-inline' http://widget.surveymonkey.com "
        "https://ajax.googleapis.com https://www.google-analytics.com data:;"
        "connect-src 'self' https://www.google-analytics.com;"
        "style-src 'self' 'unsafe-inline';"
        "img-src 'self' https://www.google-analytics.com;"
        "font-src 'self' data:"))
    return response


def register_errorhandlers(app):
    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)

        if re.match(r"/cms", request.path):
            return render_template("error/{0}.html".format(error_code)), error_code
        else:
            return render_template("static_site/error/{0}.html".format(error_code)), error_code

    for errcode in [400, 401, 403, 404, 500]:
        # add more codes if we create templates for them
        app.errorhandler(errcode)(render_error)
    return None


def setup_sqreen_audit(app):
    from application.audit.auditor import record_login
    from flask_login import user_logged_in

    user_logged_in.connect(record_login, app)


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
        log_record.user_id = -1 if current_user.is_anonymous else current_user.user_name()
        return True

import datetime
import json
import os
import pathlib
import re
import sys
import logging

from jinja2 import StrictUndefined
from jinja2.ext import do as jinja_do

from flask import Flask, render_template, request, send_from_directory, g
from flask_security import SQLAlchemyUserDatastore, Security, current_user
from raven.contrib.flask import Sentry

from application import csrf, db, mail
from application.auth.models import User
from application.auth.forms import LoginForm
from application.data.standardisers.ethnicity_classification_finder_builder import (
    ethnicity_classification_finder_from_file,
)
from application.cms.exceptions import InvalidPageHierarchy, PageNotFoundException
from application.cms.file_service import FileService
from application.cms.filters import (
    format_approve_button,
    format_friendly_date,
    format_friendly_datetime,
    format_friendly_short_date,
    format_friendly_short_date_with_year,
    format_status,
    html_line_breaks,
    index_of_last_initial_zero,
    yesno,
    models_to_dicts,
    url_with_line_breaks,
)
from application.cms.dimension_service import dimension_service
from application.cms.models import TESTING_SPACE_SLUG
from application.cms.page_service import page_service
from application.cms.scanner_service import scanner_service
from application.cms.upload_service import upload_service
from application.cms.utils import get_form_errors
from application.dashboard.trello_service import trello_service

from application.static_site.filters import (
    render_markdown,
    filesize,
    value_filter,
    flatten,
    version_filter,
    flatten_chart,
    strip_trailing_slash,
    join_enum_display_names,
    slugify_value,
    format_iso8601_date,
    html_params,
)
from application.utils import get_bool


def create_app(config_object):
    from application.static_site import static_site_blueprint
    from application.cms import cms_blueprint
    from application.admin import admin_blueprint
    from application.api import api_blueprint
    from application.register import register_blueprint
    from application.auth import auth_blueprint
    from application.dashboard import dashboard_blueprint
    from application.review import review_blueprint
    from application.redirects import redirects_blueprint

    if isinstance(config_object, str):
        from application.config import DevConfig, Config, TestConfig

        if config_object.lower().startswith("production"):
            config_object = Config
        elif config_object.lower().startswith("dev"):
            config_object = DevConfig
        elif config_object.lower().startswith("test"):
            config_object = TestConfig
        else:
            raise ValueError(f"Invalid config name passed into create_app: {config_object}")

    app = Flask(__name__)
    app.config.from_object(config_object)
    app.file_service = FileService()
    app.file_service.init_app(app)

    csrf.init_app(app)
    page_service.init_app(app)
    upload_service.init_app(app)
    scanner_service.init_app(app)
    dimension_service.init_app(app)

    trello_service.init_app(app)
    trello_service.set_credentials(config_object.TRELLO_API_KEY, config_object.TRELLO_API_TOKEN)

    db.init_app(app)

    app.url_map.strict_slashes = False

    app.classification_finder = ethnicity_classification_finder_from_file(
        config_object.ETHNICITY_CLASSIFICATION_FINDER_LOOKUP,
        config_object.ETHNICITY_CLASSIFICATION_FINDER_CLASSIFICATIONS,
    )

    # Load build info from JSON file
    current_file_path = pathlib.Path(__file__)
    repo_root_dir = current_file_path.parent.parent.resolve()
    f = open(f'{repo_root_dir}/build-info.json')
    build_info_string = f.read()
    f.close()
    build_info = json.loads(build_info_string)

    @app.before_request
    def make_before_request():
        g.build_info = build_info

    # Note not using Flask-Security role model
    user_datastore = SQLAlchemyUserDatastore(db, User, None)
    Security(app, user_datastore, login_form=LoginForm)

    if os.environ.get("SENTRY_DSN") is not None:
        Sentry(app, dsn=os.environ["SENTRY_DSN"])

    app.register_blueprint(cms_blueprint)
    app.register_blueprint(static_site_blueprint)
    app.register_blueprint(api_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(register_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(review_blueprint)
    app.register_blueprint(redirects_blueprint)

    # To stop url clash between this and the measure page url (which is made of four variables.
    # See: https://stackoverflow.com/questions/17135006/url-routing-conflicts-for-static-files-in-flask-dev-server
    @app.route("/static/<path:subdir1>/<subdir2>/<file_name>")
    def static_subdir(subdir1, subdir2, file_name):
        file_path = "%s/%s/%s" % (subdir1, subdir2, file_name)
        return send_from_directory("static", file_path)

    register_errorhandlers(app)
    app.after_request(harden_app)

    # Make sure all variables referenced in templates are explicitly defined
    app.jinja_env.undefined = StrictUndefined

    # Render jinja templates with less whitespace; applies to both CMS and static build
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.jinja_env.add_extension(jinja_do)

    app.add_template_filter(format_approve_button)
    app.add_template_filter(render_markdown)
    app.add_template_filter(filesize)
    app.add_template_filter(format_friendly_date)
    app.add_template_filter(format_friendly_datetime)
    app.add_template_filter(format_friendly_short_date)
    app.add_template_filter(format_friendly_short_date_with_year)
    app.add_template_filter(format_status)
    app.add_template_filter(value_filter)
    app.add_template_filter(flatten)
    app.add_template_filter(flatten_chart)
    app.add_template_filter(version_filter)
    app.add_template_filter(strip_trailing_slash)
    app.add_template_filter(join_enum_display_names)
    app.add_template_filter(slugify_value)
    app.add_template_filter(format_iso8601_date)
    app.add_template_filter(index_of_last_initial_zero)
    app.add_template_filter(html_params)
    app.add_template_filter(yesno)
    app.add_template_filter(models_to_dicts)
    app.add_template_filter(html_line_breaks)
    app.add_template_filter(url_with_line_breaks)

    # There is a CSS caching problem in chrome
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 10

    setup_app_logging(app, config_object)

    if os.environ.get("SQREEN_TOKEN") is not None:
        setup_sqreen_audit(app)

    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app)

    mail.init_app(app)

    def jinja_raise_exception(message):
        raise RuntimeError(message)

    @app.context_processor
    def inject_globals():
        from application.auth.models import (
            COPY_MEASURE,
            CREATE_MEASURE,
            CREATE_VERSION,
            DELETE_MEASURE,
            MANAGE_SYSTEM,
            MANAGE_USERS,
            MANAGE_DATA_SOURCES,
            ORDER_MEASURES,
            PUBLISH,
            READ,
            UPDATE_MEASURE,
            VIEW_DASHBOARDS,
            MANAGE_TOPICS,
        )

        return dict(
            COPY_MEASURE=COPY_MEASURE,
            CREATE_MEASURE=CREATE_MEASURE,
            CREATE_VERSION=CREATE_VERSION,
            DELETE_MEASURE=DELETE_MEASURE,
            MANAGE_SYSTEM=MANAGE_SYSTEM,
            MANAGE_USERS=MANAGE_USERS,
            MANAGE_DATA_SOURCES=MANAGE_DATA_SOURCES,
            ORDER_MEASURES=ORDER_MEASURES,
            PUBLISH=PUBLISH,
            READ=READ,
            UPDATE_MEASURE=UPDATE_MEASURE,
            VIEW_DASHBOARDS=VIEW_DASHBOARDS,
            TESTING_SPACE_SLUG=TESTING_SPACE_SLUG,
            get_content_security_policy=get_content_security_policy,
            current_timestamp=datetime.datetime.now().isoformat(),
            get_form_errors=get_form_errors,
            static_mode=get_bool(request.args.get("static_mode", app.config["STATIC_MODE"])),
            raise_exception=jinja_raise_exception,
            MANAGE_TOPICS=MANAGE_TOPICS,
        )

    return app


def get_content_security_policy(allow_google_custom_search=False):
    content_security_policy = (
        "default-src 'self';"
        "script-src 'self' 'unsafe-inline' http://widget.surveymonkey.com "
        "https://ajax.googleapis.com https://www.google-analytics.com https://www.googletagmanager.com "
        "{additional_script_src} data:;"
        "connect-src 'self' https://www.google-analytics.com;"
        "style-src 'self' 'unsafe-inline' {additional_style_src};"
        "img-src 'self' https://www.google-analytics.com {additional_img_src};"
        "font-src 'self' data:;"
        "{additional_other_src}"
    )

    additional_script_src = (
        (
            "'unsafe-eval' http://cse.google.com https://cse.google.com https://www.google.com "
            "https://www.googleapis.com "
        )
        if allow_google_custom_search
        else ""
    )
    additional_style_src = ("'unsafe-eval' https://www.google.com") if allow_google_custom_search else ""
    additional_img_src = (
        (
            "'unsafe-inline' http://clients1.google.com https://www.googleapis.com "
            "http://www.google.com https://encrypted-tbn3.gstatic.com https://ssl.gstatic.com"
        )
        if allow_google_custom_search
        else ""
    )
    additional_other_src = ("frame-src 'self' https://cse.google.com;") if allow_google_custom_search else ""

    return content_security_policy.format(
        additional_script_src=additional_script_src,
        additional_style_src=additional_style_src,
        additional_img_src=additional_img_src,
        additional_other_src=additional_other_src,
    )


#  https://www.owasp.org/index.php/List_of_useful_HTTP_headers
def harden_app(response):
    allow_google_custom_search = getattr(response, "_allow_google_custom_search_in_csp", False)

    response.headers.add("X-Frame-Options", "deny")
    response.headers.add("X-Content-Type-Options", "nosniff")
    response.headers.add("X-XSS-Protection", "1; mode=block")
    response.headers.add(
        "Content-Security-Policy", get_content_security_policy(allow_google_custom_search=allow_google_custom_search)
    )
    response.headers.add("X-Permitted-Cross-Domain-Policies", "none")

    return response


def register_errorhandlers(app):
    def what_you_asked_for_is_not_there_handler(error):
        return render_template("error/404.html"), 404

    app.errorhandler(InvalidPageHierarchy)(what_you_asked_for_is_not_there_handler)
    app.errorhandler(PageNotFoundException)(what_you_asked_for_is_not_there_handler)

    def render_error(error):
        # Try to get the `code` attribute (which will exist for HTTPExceptions); use 500 if no code found
        error_code = getattr(error, "code", None) or 500
        error_message = getattr(error, "description", "")

        if re.match(r"/cms", request.path):
            return render_template("error/{0}.html".format(error_code), message=error_message), error_code
        else:
            return (
                render_template("static_site/error/major-errors/{0}.html".format(error_code), message=error_message),
                error_code,
            )

    for errcode in [400, 401, 403, 404, 500]:
        # add more codes if we create templates for them
        app.errorhandler(errcode)(render_error)
    return None


def setup_sqreen_audit(app):
    from application.audit.auditor import record_login
    from flask_login import user_logged_in

    user_logged_in.connect(record_login, app)


def setup_app_logging(app, config):
    log_format = '%(ip)s - [%(asctime)s] %(levelname)s "%(method)s %(url)s" - [user:%(user_id)s - %(message)s]'
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(HasIPFilter())  # Only log from this handler if it's an actual (external) request.

    app.logger.addFilter(ContextualFilter())  # All log records get the request context
    app.logger.addHandler(handler)
    app.logger.setLevel(config.LOG_LEVEL)


class ContextualFilter(logging.Filter):
    def filter(self, log_record):
        log_record.url = request.path
        log_record.method = request.method
        log_record.ip = request.environ.get("REMOTE_ADDR")
        log_record.user_id = -1 if current_user.is_anonymous else current_user.user_name()
        return True


class HasIPFilter(logging.Filter):
    def filter(self, log_record):
        return True if request.environ.get("REMOTE_ADDR", False) else False

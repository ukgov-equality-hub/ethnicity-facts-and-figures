import csv
import hashlib
import json
import logging
import os
import sys
import time
from datetime import date
from functools import wraps
from io import StringIO

from flask import abort, current_app, flash, has_request_context, render_template, url_for
from flask_login import current_user
from flask_mail import Message
from itsdangerous import SignatureExpired, TimestampSigner, URLSafeTimedSerializer
from slugify import slugify

from application import mail


def setup_module_logging(logger, level):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    if len(logger.handlers) > 1:
        logger.warning("The same logger may have been initialised multiple times.")

    return logger


def get_bool(param):
    if str(param).lower().strip() in ["true", "t", "yes", "y", "on", "1"]:
        return True
    elif str(param).lower().strip() in ["false", "f", "no", "n", "off", "0"]:
        return False
    return False


# This should be placed after login_required decorator as it needs authenticated user
def user_has_access(f):
    from application.cms.page_service import page_service

    @wraps(f)
    def decorated_function(*args, **kwargs):
        topic_slug = kwargs.get("topic_slug")
        subtopic_slug = kwargs.get("subtopic_slug")
        measure_slug = kwargs.get("measure_slug")
        measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

        if current_user.is_authenticated and measure_slug is not None and current_user.can_access_measure(measure):
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function


# This should be placed after login_required decorator as it needs authenticated user
def user_can(capabilibity):
    def can_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated and current_user.can(capabilibity):
                return f(*args, **kwargs)
            else:
                return abort(403)

        return decorated_function

    return can_decorator


class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def get_csv_data_for_download(filename):

    rows = []
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                rows.append(row)

    except UnicodeDecodeError:
        rows = []  # Reset rows to be empty before attempting to read the file again, to avoid duplication
        with open(filename, "r", encoding="iso-8859-1") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                rows.append(row)

    except Exception as e:
        message = "error with file %s" % filename
        print(message, e)
        raise e

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")

        for row in rows:
            writer.writerow(row)

        return output.getvalue()


def generate_token(email, app):
    signer = TimestampSigner(app.config["SECRET_KEY"])
    return signer.sign(email).decode("utf8")


def check_token(token, app):
    signer = TimestampSigner(app.config["SECRET_KEY"])
    try:
        email = signer.unsign(token, max_age=app.config["TOKEN_MAX_AGE_SECONDS"])
        if isinstance(email, bytes):
            email = email.decode("utf-8")
        return email
    except SignatureExpired as e:
        current_app.logger.info("token expired %s" % e)
        return None


def create_and_send_activation_email(email, app, devmode=False):
    token = generate_token(email, app)
    confirmation_url = url_for("register.confirm_account", token=token, _external=True)

    if devmode:
        return confirmation_url

    html = render_template("admin/confirm_account.html", confirmation_url=confirmation_url, user=email)
    try:
        send_email(
            app.config["RDU_EMAIL"], email, html, "Access to the Ethnicity Facts and Figures content management system", { 'confirmation_url': confirmation_url, 'user': email }
        )
        flash("User account invite sent to: %s." % email)
    except Exception as ex:
        flash("Failed to send invite to: %s" % email, "error")
        app.logger.error(ex)


def send_reactivation_email(email, app, devmode=False):
    token = generate_token(email, app)
    confirmation_url = url_for("register.confirm_account", token=token, _external=True)

    if devmode:
        return confirmation_url

    html = render_template("admin/reactivate_account.html", confirmation_url=confirmation_url, user=email)
    try:
        send_email(
            app.config["RDU_EMAIL"], email, html, "Your Ethnicity facts and figures account has been deactivated", { 'confirmation_url': confirmation_url }
        )
    except Exception as ex:
        app.logger.error(ex)


def send_email(sender, email, message, subject, data = ''):
    GOV_UK_NOTIFY_API_KEY = os.environ.get("GOV_UK_NOTIFY_API_KEY", "")
    if GOV_UK_NOTIFY_API_KEY != '':
        from notifications_python_client.notifications import NotificationsAPIClient
        notifications_client = NotificationsAPIClient(GOV_UK_NOTIFY_API_KEY)

        template_id = ''
        if subject == 'Access to the Ethnicity Facts and Figures content management system':
            template_id = 'b74efa99-932f-4072-9665-fec8a4b42297'
        elif subject == 'Your Ethnicity facts and figures account has been deactivated':
            template_id = 'c8f3ece1-bb6c-45b2-bc16-7bb1c286c9a8'

        response = notifications_client.send_email_notification(
            email_address=email,
            template_id=template_id,
            personalisation=data
        )
    else:
        msg = Message(html=message, subject=subject, sender=sender, recipients=[email])
        mail.send(msg)


def write_dimension_csv(dimension):
    if "table" in dimension:
        source_data = dimension["table"]["data"]
    elif "chart" in dimension:
        source_data = dimension["chart"]["data"]
    else:
        source_data = [[]]

    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def write_dimension_tabular_csv(dimension):
    if "tabular" in dimension:
        source_data = dimension["tabular"]["data"]
    else:
        source_data = [[]]

    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def generate_review_token(page_id):
    key = os.environ.get("SECRET_KEY")
    serializer = URLSafeTimedSerializer(key)
    return serializer.dumps(str(page_id))


def decode_review_token(token, config):
    key = config["SECRET_KEY"]
    serializer = URLSafeTimedSerializer(key)
    seconds_in_day = 24 * 60 * 60
    max_age_seconds = seconds_in_day * config.get("PREVIEW_TOKEN_MAX_AGE_DAYS")
    decoded_token = serializer.loads(token, max_age=max_age_seconds)

    # TODO: Once all guid-based tokens have expired adjust this to not split and return ID only
    page_id, page_version = decoded_token.split("|") if "|" in decoded_token else (decoded_token, None)
    return page_id, page_version


def get_token_age(token, config):
    key = config["SECRET_KEY"]
    serializer = URLSafeTimedSerializer(key)
    token_created = serializer.loads(token, return_timestamp=True)[1]
    return token_created


def create_guid(value):
    hash = hashlib.sha1()
    hash.update("{}{}".format(str(time.time()), slugify(value)).encode("utf-8"))
    return hash.hexdigest()


class TimedExecution:
    def __init__(self, description, print_=True):
        self.description = description
        self.print = print_

        self.log = print if not has_request_context() else current_app.logger.debug

    def __enter__(self):
        self.start = time.time()

        if self.print:
            self.log(f"ENTER: {self.description}")

        return self

    def __exit__(self, type, value, traceback):
        execution_time = time.time() - self.start

        if self.print:
            self.log(f"EXIT: {self.description} ({execution_time}s elapsed)")

        return execution_time


def cleanup_filename(filename):
    return slugify(filename)

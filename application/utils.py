import csv
import json
import sys
import os
import logging
from datetime import date

from flask_mail import Message
from functools import wraps

from io import StringIO
from flask import abort, current_app, url_for, render_template, flash
from flask_login import current_user
from itsdangerous import TimestampSigner, SignatureExpired

from application import mail


def setup_module_logging(logger, level):
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def get_bool(param):
    if str(param).lower().strip() in ['true', 't', 'yes', 'y', 'on', '1']:
        return True
    elif str(param).lower().strip() in ['false', 'f', 'no', 'n', 'off', '0']:
        return False
    return False


def internal_user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.is_internal_user():
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.is_admin():
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


class DateEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def get_content_with_metadata(filename, page):
    source = os.environ.get('RDU_SITE', 'https://www.ethnicity-facts-figures.service.gov.uk')
    metadata = [['Title', page.title],
                ['Location', page.geographic_coverage],
                ['Time period', page.time_covered],
                ['Data source', page.department_source],
                ['Data source link', page.source_url],
                ['Source', source],
                ['Last updated', page.last_update_date]]

    try:
        with open(filename) as f:
            rows = []
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                rows.append(row)

        with StringIO() as output:
            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

            for m in metadata:
                writer.writerow(m)

            for row in rows:
                writer.writerow(row)

            content = output.getvalue()

        return content

    except Exception as e:
        print(e)


def generate_token(email, app):
    signer = TimestampSigner(app.config['SECRET_KEY'])
    return signer.sign(email).decode('utf8')


def check_token(token, app):
    signer = TimestampSigner(app.config['SECRET_KEY'])
    try:
        email = signer.unsign(token,
                              max_age=app.config['TOKEN_MAX_AGE_SECONDS'])
        if isinstance(email, bytes):
            email = email.decode('utf-8')
        return email
    except SignatureExpired as e:
        current_app.logger.info('token expired %s' % e)
        return None


def create_and_send_activation_email(email, app):
    token = generate_token(email, app)
    confirmation_url = url_for('register.confirm_account',
                               token=token,
                               _external=True)
    html = render_template('admin/confirm_account.html', confirmation_url=confirmation_url, user=current_user)
    try:
        send_email(app.config['RDU_EMAIL'], email, html)
        flash("User account invite sent to: %s." % email)
    except Exception as ex:
        flash("Failed to send invite to: %s" % email, 'error')
        app.logger.error(ex)


def send_email(sender, email, message):
    msg = Message(html=message,
                  subject="Access to the RDU CMS",
                  sender=sender,
                  recipients=[email])
    mail.send(msg)

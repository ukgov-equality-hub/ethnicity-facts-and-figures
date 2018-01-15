import codecs
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

    rows = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                rows.append(row)

    except UnicodeDecodeError as e:
        with open(filename, 'r', encoding='iso-8859-1') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                rows.append(row)

    except Exception as e:
        message = 'error with file %s' % filename
        print(message, e)
        raise e

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')

        for m in metadata:
            writer.writerow(m)

        for row in rows:
            writer.writerow(row)

        return output.getvalue()


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


def create_and_send_activation_email(email, app, devmode=False):
    token = generate_token(email, app)
    confirmation_url = url_for('register.confirm_account',
                               token=token,
                               _external=True)

    if devmode:
        return confirmation_url

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


def write_dimension_csv(dimension):
    if 'table' in dimension:
        source_data = dimension['table']['data']
    elif 'chart' in dimension:
        source_data = dimension['chart']['data']
    else:
        source_data = [[]]

    metadata = get_dimension_metadata(dimension)
    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('')
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def write_dimension_tabular_csv(dimension):
    if 'tabular' in dimension:
        source_data = dimension['tabular']['data']
    else:
        source_data = [[]]

    metadata = get_dimension_metadata(dimension)

    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('')
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def get_dimension_metadata(dimension):
    source = os.environ.get('RDU_SITE', '')

    if dimension['context']['last_update'] != '':
        date = dimension['context']['last_update']
    elif dimension['context']['publication_date'] != '':
        date = dimension['context']['publication_date']
    else:
        date = ''

    return [['Title', dimension['context']['dimension']],
            ['Location', dimension['context']['location']],
            ['Time period', dimension['context']['time_period']],
            ['Data source', dimension['context']['source_text']],
            ['Data source link', dimension['context']['source_url']],
            ['Source', source],
            ['Last updated', date]
            ]

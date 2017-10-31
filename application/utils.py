import csv
import json
import sys
import os
import logging
from datetime import date
from functools import wraps

from io import StringIO
from flask import abort, current_app
from flask_login import current_user
from itsdangerous import TimestampSigner, SignatureExpired


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


def get_content_with_metadata(file_contents, page):

    source = os.environ.get('RDU_SITE', '')
    metadata = [['Title', page.title],
                ['Location', page.geographic_coverage],
                ['Time period', page.time_covered],
                ['Data source', page.department_source],
                ['Data source link', page.source_url],
                ['Source', source],
                ['Last updated', page.last_update_date]]

    file_contents = file_contents.splitlines()
    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('\n')
        for encoding in ['utf-8', 'iso-8859-1']:
            try:
                for line in file_contents:
                    output.write(line.decode(encoding))
                    output.write('\n')
                break
            except Exception as e:
                print(e)
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

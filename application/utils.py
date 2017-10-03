import json
import sys
import logging
from datetime import date
from functools import wraps

from flask import abort
from flask_login import current_user


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


class DateEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def get_content_with_metadata(file_contents, page):

    title = page.title.replace(',', '') if page.title else ''
    time_covered = page.title.replace(',', '') if page.title else ''
    geographic_coverage = page.time_covered.replace(',', '') if page.time_covered else ''
    source_text = page.source_text.replace(',', '') if page.source_text else ''
    department_source = page.department_source.replace(',', '') if page.department_source else ''
    last_update_date = page.last_update_date.replace(',', '') if page.last_update_date else ''

    meta_data = "Title, %s\nTime period, %s\nLocation, %s\nSource, %s\nDepartment, %s\nLast update, %s\n" \
                % (title,
                   time_covered,
                   geographic_coverage,
                   source_text,
                   department_source,
                   last_update_date)

    file_contents = file_contents.splitlines()
    response_file_content = ''
    for encoding in ['utf-8', 'iso-8859-1']:
        try:
            for line in file_contents:
                response_file_content += '\n' + line.decode(encoding)
            return (meta_data + response_file_content).encode(encoding)
        except Exception as e:
            print(e)
    else:
        return ''

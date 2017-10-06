import csv
import json
import sys
import logging
from datetime import date
from functools import wraps

from io import StringIO
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

    metadata = [['Title', page.title],
                ['Time period', page.time_covered],
                ['Location', page.geographic_coverage],
                ['Source', page.source_text],
                ['Department', page.department_source],
                ['Last update', page.last_update_date]
                ]
    file_contents = file_contents.splitlines()
    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow('\n')
        for encoding in ['utf-8', 'iso-8859-1']:
            try:
                field_names = file_contents[0].decode(encoding).split(',')
                writer.writerow(field_names)
                for line in file_contents[1:]:
                    content = line.decode(encoding).split(',')
                    content.append('\n')
                    writer.writerow(content)
                break
            except Exception as e:
                print(e)
        return output.getvalue()

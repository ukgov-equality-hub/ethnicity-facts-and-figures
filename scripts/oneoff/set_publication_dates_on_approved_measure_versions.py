#!/usr/bin/env python


import csv
import sys

sys.path.insert(0, ".")  # noqa

from application import db
from application.cms.models import MeasureVersion
from application.cms.page_service import page_service
from application.config import DevConfig
from application.factory import create_app

app = create_app(DevConfig)
with app.app_context():

    sql = """
SELECT measure_version.id
FROM   measure_version
WHERE status = 'APPROVED' AND published_at IS NULL
AND external_edit_summary = 'Some headings have been changed. No data or commentary has been updated.'
"""

    result = db.session.execute(sql)

    for row in result:

        measure_version = MeasureVersion.query.get(row[0])
        page_service.mark_measure_version_published(measure_version)

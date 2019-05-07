#!/usr/bin/env python


import sys
import csv

sys.path.insert(0, ".")  # noqa

from application.config import DevConfig
from application import db
from application.factory import create_app
from application.dashboard.data_helpers import _calculate_short_title


app = create_app(DevConfig)
with app.app_context():

    sql = """
SELECT dimension.guid        AS dimension_id,
       measure_version.title AS measure_title,
       dimension.title       AS dimension_title
FROM   dimension
       LEFT JOIN measure_version
              ON dimension.measure_version_id = measure_version.id
       INNER JOIN latest_published_measure_versions
               ON measure_version.id = latest_published_measure_versions.id
ORDER  BY measure_version.title,
          dimension.position
"""

    result = db.session.execute(sql)

    with open("dimension_titles.csv", mode="w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(("dimension_id", "measure_title", "current_dimension_title", "new_dimension_title"))

        for row in result:
            writer.writerow(
                (
                    row["dimension_id"],
                    row["measure_title"],
                    row["dimension_title"],
                    _calculate_short_title(row["measure_title"], row["dimension_title"]),
                )
            )

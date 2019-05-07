#!/usr/bin/env python


import sys
import csv

sys.path.insert(0, ".")

from application import db
from application.factory import create_app
from application.config import DevConfig

from application.dashboard.data_helpers import _calculate_short_title


app = create_app(DevConfig)
with app.app_context():

    sql = "select dimension.guid as dimension_id, measure_version.title as measure_title, dimension.title as dimension_title from dimension left join measure_version on dimension.measure_version_id = measure_version.id inner join latest_published_measure_versions on measure_version.id = latest_published_measure_versions.id order by measure_version.title, dimension.position"  # noqa

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

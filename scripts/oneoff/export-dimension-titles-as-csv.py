#!/usr/bin/env python


import sys
import csv

from application import db
from application.factory import create_app
from application.config import DevConfig

sys.path.insert(0, ".")


def _calculate_short_title(page_title, dimension_title):
    # Case 1 - try stripping the dimension title
    low_title = dimension_title.lower()
    if low_title.find(page_title.lower()) == 0:
        return dimension_title[len(page_title) + 1 :]

    # Case 2 - try cutting using the last by
    by_pos = dimension_title.rfind("by")
    if by_pos >= 0:
        return dimension_title[by_pos:]

    # Case else - just return the original
    return dimension_title


app = create_app(DevConfig)
with app.app_context():

    sql = "select dimension.guid as dimension_id, measure_version.title as measure_title, dimension.title as dimension_title from dimension left join measure_version on dimension.measure_version_id = measure_version.id inner join latest_published_measure_versions on measure_version.id = latest_published_measure_versions.id order by measure_version.title, dimension.position"  # noqa

    result = db.session.execute(sql)
    db.session.commit()

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

#!/usr/bin/env python

"""
This script was used to work out which tables were affected by a bug that transposed cells on grouped tables if an
ordering wasn't specified explicitly and the data was provided in an inconsistent format.

See https://trello.com/c/mrtsskDU/1103 for additional details.
"""

import logging
from collections import defaultdict
import pprint
import sys

sys.path.insert(0, ".")

from flask import url_for

from application.config import DevConfig
from application.factory import create_app
from application.cms.models import Dimension


LOG_LEVEL = logging.INFO


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler(sys.stdout))


def measure_page_url_from_dimension(dimension):
    measure_page = dimension.page
    subtopic_page = measure_page.parent
    topic_page = subtopic_page.parent
    return url_for(
        "static_site.measure_version",
        topic_uri=topic_page.uri,
        subtopic_uri=subtopic_page.uri,
        measure_uri=measure_page.uri,
        version=dimension.page_version,
        _external=True,
    )


def edit_table_url_from_dimension(dimension, tablebuilder2=False):
    measure_page = dimension.page
    subtopic_page = measure_page.parent
    topic_page = subtopic_page.parent
    return url_for(
        "cms.create_table" if tablebuilder2 else "cms.create_table_original",
        topic_uri=topic_page.uri,
        subtopic_uri=subtopic_page.uri,
        measure_uri=measure_page.guid,
        version=dimension.page_version,
        dimension_guid=dimension.guid,
        _external=True,
    )


class SkipDimensionTable(Exception):
    pass


def get_ethnicity_and_category_column_idx(dimension, tablebuilder2=False):
    log_prefix = "TB2" if tablebuilder2 else "TB1"
    if tablebuilder2:
        source_data = dimension.table_2_source_data
        headers = source_data["data"][0]
        table_options = source_data.get("tableOptions", {})

        if (
            source_data
            and source_data["tableOptions"]
            and source_data["tableOptions"]["data_style"] == "ethnicity_as_column"
            and source_data["tableOptions"]["order"] == "[None]"
        ):
            ethnicity_header_index = 0
            subgroup_header_index = 0

            for idx, header in enumerate(headers):
                if header.lower() == "ethnicity" or header.lower() == "ethnic group":
                    ethnicity_column_idx = idx
                    break
            else:
                logger.debug(
                    log_prefix
                    + f"Unable to find ethnicity column for {dimension.guid} (table_source_data): {source_data['data'][0]}"
                )
                logger.debug(edit_table_url_from_dimension(dimension, tablebuilder2=tablebuilder2))
                raise SkipDimensionTable

        else:
            raise SkipDimensionTable

        try:
            category_column_idx = headers.index(table_options["selection"])
        except ValueError:
            raise SkipDimensionTable

    else:
        source_data = dimension.table_source_data
        headers = source_data["data"][0]
        table_options = source_data.get("tableOptions", {})
        logger.debug("Headers: " + str(source_data["data"][0]))

        if len(headers) == 1 and headers[0] == "":
            logger.debug(log_prefix + f"Skipping dimension {dimension.guid} with no table headers")
            raise SkipDimensionTable

        if table_options["table_order_column"] == "[None]":
            for idx, header in enumerate(headers):
                if header.lower() == "ethnicity" or header.lower() == "ethnic group":
                    ethnicity_column_idx = idx
                    break
            else:
                logger.debug(
                    log_prefix
                    + f"Unable to find ethnicity column for {dimension.guid} (table_source_data): {source_data['data'][0]}"
                )
                logger.debug(log_prefix + edit_table_url_from_dimension(dimension, tablebuilder2=tablebuilder2))
                raise SkipDimensionTable

        else:
            raise SkipDimensionTable

        try:
            category_column_idx = headers.index(table_options["table_category_column"])
        except ValueError:
            raise SkipDimensionTable

    return ethnicity_column_idx, category_column_idx


def find_inconsistent_grouped_table_dimensions(app):
    with app.app_context():
        dimensions = Dimension.query.all()

        for dimension in dimensions:
            logger.debug(f"Dimension {dimension.guid}")
            for tablebuilder2 in [False, True]:
                logger.debug(f"tablebuilder2: {tablebuilder2}")
                log_prefix = "TB2: " if tablebuilder2 else "TB1: "

                if not tablebuilder2 and dimension.table_source_data and not dimension.table_2_source_data:
                    source_data = dimension.table_source_data
                    try:
                        ethnicity_column_idx, category_column_idx = get_ethnicity_and_category_column_idx(
                            dimension, tablebuilder2=tablebuilder2
                        )
                    except SkipDimensionTable:
                        continue

                elif tablebuilder2 and dimension.table_2_source_data:
                    source_data = dimension.table_2_source_data
                    try:
                        ethnicity_column_idx, category_column_idx = get_ethnicity_and_category_column_idx(
                            dimension, tablebuilder2=tablebuilder2
                        )
                    except SkipDimensionTable:
                        continue

                else:
                    logger.debug(log_prefix + f"Skipping dimension {dimension.guid} with no table data")
                    continue

                if (
                    ethnicity_column_idx != 0 or category_column_idx != 0
                ) and ethnicity_column_idx != category_column_idx:
                    grouped_by_ethnicity = defaultdict(list)

                    for row in source_data["data"][1:]:
                        logger.debug(row)
                        logger.debug(str(ethnicity_column_idx) + " " + str(category_column_idx))
                        grouped_by_ethnicity[row[ethnicity_column_idx].strip().lower()].append(row[category_column_idx])

                    values = [x for x in grouped_by_ethnicity.values()]
                    if not all(value == values[0] for value in values):
                        if dimension.page.has_no_later_published_versions():
                            logger.info(log_prefix + f"Mismatch on {dimension.guid} (tablebuilder2={tablebuilder2}):")
                            logger.info(log_prefix + "    " + measure_page_url_from_dimension(dimension))
                            logger.info(
                                log_prefix
                                + "    "
                                + edit_table_url_from_dimension(dimension, tablebuilder2=tablebuilder2)
                            )
                            # logger.info(log_prefix + str(pprint.pprint(grouped_by_ethnicity)))
                        else:
                            logger.debug(
                                log_prefix
                                + f"Mismatch on {dimension.guid} (tablebuilder2={tablebuilder2}): version superceded by more recent publication"
                            )

                else:
                    logger.debug(
                        log_prefix + f"tablebuilder2={tablebuilder2}: {ethnicity_column_idx}, {category_column_idx}"
                    )
                    continue


if __name__ == "__main__":
    app = create_app(DevConfig)
    find_inconsistent_grouped_table_dimensions(app)

#!/usr/bin/env python
import sys
from flask import current_app

sys.path.insert(0, ".")  # noqa: E402

from application import db
from application.cms.models import Dimension, Chart, Table
from application.config import Config
from application.data.charts import ChartObjectDataBuilder
from application.data.tables import TableObjectDataBuilder
from application.factory import create_app


def copy_chart_and_table_data(app):  # noqa: C901
    with app.app_context():
        try:
            count = 0
            chart_failures = 0
            table_failures = 0
            for dimension in Dimension.query.all():
                # If there is a chart object, copy it to the chart table
                if dimension.chart:
                    # Create a Chart() if necessary
                    if dimension.dimension_chart is None:
                        dimension.dimension_chart = Chart()

                    # Don't overwrite if it already exists
                    if dimension.dimension_chart.chart_object is None:
                        dimension.dimension_chart.chart_object = dimension.chart

                    if dimension.chart_2_source_data is not None:
                        # If there is already a version 2 chart settings, copy settings straight across
                        # But don't overwrite if it already exists
                        if dimension.dimension_chart.settings_and_source_data is None:
                            dimension.dimension_chart.settings_and_source_data = dimension.chart_2_source_data
                    else:
                        # Assume there are version 1 settings if no version 2; convert it and copy it across
                        try:
                            version_2_settings = ChartObjectDataBuilder.upgrade_v1_to_v2(
                                dimension.chart, dimension.chart_source_data
                            )
                            # Don't overwrite if it already exists
                            if dimension.dimension_chart.settings_and_source_data is None:
                                dimension.dimension_chart.settings_and_source_data = version_2_settings
                        except Exception as e:
                            chart_failures += 1
                            print(f"Error copying chart for {dimension.title} ({dimension.guid})")
                            print(f"  CHART EXCEPTION: {type(e)}: {e}")

                # If there is a table object, copy it to the table table
                if dimension.table:
                    # Create a Table() if necessary
                    if dimension.dimension_table is None:
                        dimension.dimension_table = Table()

                    # Don't overwrite if it already exists
                    if dimension.dimension_table.table_object is None:
                        dimension.dimension_table.table_object = dimension.table

                    if dimension.table_2_source_data is not None:
                        # If there is already a version 2 table settings, copy settings straight across
                        # But don't overwrite if it already exists
                        if dimension.dimension_table.settings_and_source_data is None:
                            dimension.dimension_table.settings_and_source_data = dimension.table_2_source_data
                    else:
                        # Assume there are version 1 settings if no version 2; convert it and copy it across
                        try:
                            version_2_settings = TableObjectDataBuilder.upgrade_v1_to_v2(
                                dimension.table, dimension.table_source_data, current_app.dictionary_lookup
                            )
                            # Don't overwrite if it already exists
                            if dimension.dimension_table.settings_and_source_data is None:
                                dimension.dimension_table.settings_and_source_data = version_2_settings
                        except Exception as e:
                            table_failures += 1
                            print(f"Error copying table for {dimension.title} ({dimension.guid})")
                            print(f"  TABLE EXCEPTION: {type(e)}: {e}")

                count += 1

            db.session.commit()
            print(f"Total: {count}, Chart failures: {chart_failures}, Table failures: {table_failures}")

        except Exception as e:
            print(e)
            db.session.rollback()
            raise e

        finally:
            db.session.close()


if __name__ == "__main__":
    app = create_app(Config())
    copy_chart_and_table_data(app)

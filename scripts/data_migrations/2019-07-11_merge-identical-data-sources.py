#!/usr/bin/env python

import sys

sys.path.insert(0, ".")  # noqa

from sqlalchemy import func

from application import db
from application.config import Config
from application.factory import create_app
from application.cms.models import DataSource


def merge_identical_duplicate_data_sources(app):
    with app.app_context():
        count = 0

        DataSource.query.update({DataSource.purpose: func.rtrim(DataSource.purpose, " \r")}, synchronize_session=False)

        try:
            all_data_source_ids = DataSource.query.with_entities(DataSource.id).all()

            for data_source_id in all_data_source_ids:
                data_source = DataSource.query.get(data_source_id)
                if data_source:
                    other_identical_data_sources = (
                        DataSource.query.filter(
                            DataSource.id != data_source.id,
                            DataSource.title == data_source.title,
                            DataSource.type_of_data == data_source.type_of_data,
                            DataSource.type_of_statistic_id == data_source.type_of_statistic_id,
                            DataSource.publisher_id == data_source.publisher_id,
                            DataSource.source_url == data_source.source_url,
                            DataSource.publication_date == data_source.publication_date,
                            DataSource.note_on_corrections_or_updates == data_source.note_on_corrections_or_updates,
                            DataSource.frequency_of_release_id == data_source.frequency_of_release_id,
                            DataSource.frequency_of_release_other == data_source.frequency_of_release_other,
                            DataSource.purpose == data_source.purpose,
                        )
                        .with_entities(DataSource.id)
                        .all()
                    )

                    print(f"Data source #{data_source.id}:")

                    if other_identical_data_sources:
                        for other_identical_data_source in other_identical_data_sources:
                            print(f"  Absorbed #{other_identical_data_source.id}")
                            count += 1

                        data_source.merge(other_identical_data_sources)

            db.session.commit()

        except Exception as e:
            print(e)
            db.session.rollback()

        finally:
            db.session.close()

    print(f"Finished. Merged {count} duplicate data sources.")


if __name__ == "__main__":
    app = create_app(Config())
    merge_identical_duplicate_data_sources(app)

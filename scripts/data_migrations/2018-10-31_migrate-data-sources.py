#!/usr/bin/env python

import sys

sys.path.insert(0, ".")

from application import db
from application.config import Config
from application.factory import create_app
from application.cms.models import MeasureVersion, DataSource


DATA_SOURCE_1_ATTRIBUTE_MAP = {
    "source_text": "title",
    "source_url": "source_url",
    "type_of_data": "type_of_data",
    "type_of_statistic_id": "type_of_statistic_id",
    "department_source_id": "publisher_id",
    "published_date": "publication_date",
    "note_on_corrections_or_updates": "note_on_corrections_or_updates",
    "frequency_id": "frequency_of_release_id",
    "frequency_other": "frequency_of_release_other",
    "data_source_purpose": "purpose",
}
DATA_SOURCE_2_ATTRIBUTE_MAP = {
    "secondary_source_1_title": "title",
    "secondary_source_1_url": "source_url",
    "secondary_source_1_type_of_data": "type_of_data",
    "secondary_source_1_type_of_statistic_id": "type_of_statistic_id",
    "secondary_source_1_publisher_id": "publisher_id",
    "secondary_source_1_date": "publication_date",
    "secondary_source_1_note_on_corrections_or_updates": "note_on_corrections_or_updates",
    "secondary_source_1_frequency_id": "frequency_of_release_id",
    "secondary_source_1_frequency_other": "frequency_of_release_other",
    "secondary_source_1_data_source_purpose": "purpose",
}


def get_page_attributes_collapsed_to_none(page, attrs_map):
    data_source_attrs = {attr: getattr(page, attr, None) for attr in attrs_map.keys()}

    for attr, value in data_source_attrs.items():
        if isinstance(value, str) and value.strip() == "":
            data_source_attrs[attr] = None

    return data_source_attrs


def create_new_data_source(page, attrs_map):
    data_source = DataSource()

    for page_data_source_name, normalised_data_source_name in attrs_map.items():
        if hasattr(data_source, normalised_data_source_name):
            setattr(data_source, normalised_data_source_name, getattr(page, page_data_source_name))
        else:
            raise AttributeError(f"Wrong attribute name for data source: {normalised_data_source_name}")

    return data_source


def migrate_data_sources(app):
    with app.app_context():
        try:
            for page in MeasureVersion.query.filter(MeasureVersion.page_type == "measure"):
                print(f"Checking data sources for {page}")

                if len(page.data_sources) < 1:
                    data_source_attrs = get_page_attributes_collapsed_to_none(page, DATA_SOURCE_1_ATTRIBUTE_MAP)

                    if any(value for value in data_source_attrs.values()):
                        print(f"Found primary data source: {data_source_attrs}")

                        new_data_source = create_new_data_source(page, DATA_SOURCE_1_ATTRIBUTE_MAP)
                        page.data_sources.append(new_data_source)

                        db.session.add(page)
                        db.session.add(new_data_source)

                if len(page.data_sources) < 2:
                    data_source_2_attrs = get_page_attributes_collapsed_to_none(page, DATA_SOURCE_2_ATTRIBUTE_MAP)

                    if any(value for value in data_source_2_attrs.values()):
                        print(f"Found secondary data source: {data_source_2_attrs}")

                        new_data_source = create_new_data_source(page, DATA_SOURCE_2_ATTRIBUTE_MAP)
                        page.data_sources.append(new_data_source)

                        db.session.add(page)
                        db.session.add(new_data_source)

            db.session.commit()

        except Exception as e:
            print(e)
            db.session.rollback()

        finally:
            db.session.close()


if __name__ == "__main__":
    app = create_app(Config())
    migrate_data_sources(app)

#!/usr/bin/env python


import csv
import sys
from argparse import ArgumentParser
from typing import List

sys.path.insert(0, ".")  # noqa

from application import db
from application.cms.page_service import page_service
from application.config import DevConfig
from application.factory import create_app

from application.auth.models import User
from application.cms.models import Dimension, NewVersionType
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


def import_dimension_titles(user_email, app, dimension_rows: List):  # noqa: C901
    STANDARD_EDIT_SUMMARY = "Updated dimension titles"
    error_count = 0

    with app.app_context():
        user = User.query.filter_by(email=user_email).one()

        for row in dimension_rows:
            dimension_guid, _, current_dimension_title, new_dimension_title = row

            try:
                dimension = Dimension.query.filter_by(guid=dimension_guid).one()
            except NoResultFound:
                error_count += 1
                continue

            measure_version = dimension.measure_version
            measure = measure_version.measure
            latest_measure_version = measure.latest_version

            draft_measure_to_update = None

            if latest_measure_version.id == measure_version.id:
                if (
                    Dimension.query.filter(
                        Dimension.measure_version_id == measure_version.id, Dimension.title == current_dimension_title
                    ).count()
                    == 1
                ):
                    draft_measure_to_update = page_service.create_measure_version(
                        measure_version, NewVersionType.MINOR_UPDATE, user
                    )
                    draft_measure_to_update.external_edit_summary = STANDARD_EDIT_SUMMARY

                else:
                    print(f"{measure_version} has multiple dimensions with the same title")

            else:
                if (
                    latest_measure_version.status == "DRAFT"
                    and latest_measure_version.external_edit_summary == STANDARD_EDIT_SUMMARY
                ):
                    draft_measure_to_update = latest_measure_version

                elif latest_measure_version.status == "APPROVED":
                    try:
                        draft_dimension = Dimension.query.filter_by(
                            measure_version_id=latest_measure_version.id, title=dimension.title
                        ).one()

                    except NoResultFound:
                        print(f"ERROR: No dimension found for {latest_measure_version}")

                    except MultipleResultsFound:
                        print(f"ERROR: Multiple dimensions found for {latest_measure_version}")

                    else:
                        if draft_dimension.title == current_dimension_title:
                            draft_measure_to_update = page_service.create_measure_version(
                                latest_measure_version, NewVersionType.MINOR_UPDATE, user
                            )
                            draft_measure_to_update.external_edit_summary = STANDARD_EDIT_SUMMARY

            if draft_measure_to_update:
                try:
                    draft_dimension = Dimension.query.filter_by(
                        measure_version_id=draft_measure_to_update.id, title=dimension.title
                    ).one()

                    if draft_dimension.title != new_dimension_title:
                        print("Updating '" + draft_dimension.title + "' to '" + new_dimension_title)

                        draft_dimension.title = new_dimension_title
                        db.session.add(draft_dimension)

                except NoResultFound:
                    print(f"ERROR: No dimension found for {draft_measure_to_update}")
                    error_count += 1

                except MultipleResultsFound:
                    print(f"ERROR: Multiple dimensions found for {draft_measure_to_update}")
                    error_count += 1

            else:
                print(
                    f"{latest_measure_version.title} ({latest_measure_version}) is in {latest_measure_version.status}"
                )
                error_count += 1

        db.session.commit()

        if error_count > 0:
            print(f"\n\n\nERRORS: {error_count}")

        return error_count


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("email", type=str, help="Email address of the user to attribute these updates to")
    parser.add_argument("dimension_csv", type=str, help="")
    args = parser.parse_args()

    app = create_app(DevConfig)

    dimension_rows = []
    with open(args.dimension_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        for row in csv_reader:
            dimension_rows.append(row)

    import_dimension_titles(user_email=args.email, app=app, dimension_rows=dimension_rows[1:])

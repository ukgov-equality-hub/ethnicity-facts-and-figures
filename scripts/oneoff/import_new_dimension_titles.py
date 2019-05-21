#!/usr/bin/env python


import csv
import sys

from argparse import ArgumentParser
from collections import defaultdict
from sqlalchemy.orm.exc import NoResultFound
from typing import List

sys.path.insert(0, ".")  # noqa

from application import db
from application.auth.models import User
from application.cms.models import Dimension, NewVersionType
from application.cms.page_service import page_service
from application.config import DevConfig
from application.factory import create_app

STANDARD_EDIT_SUMMARY = "Some headings have been changed. No data or commentary has been updated."


def import_dimension_titles(user_email, app, dimension_rows: List):  # noqa: C901
    error_count = 0

    with app.app_context():
        user = User.query.filter_by(email=user_email).one()

        dimension_guids_to_new_titles = {}
        measure_versions_to_dimension_guids = defaultdict(list)
        skip_measures = set()

        print("1. GATHERING DIMENSIONS AND MEASURES")
        # Gather all of the dimension/measure instances in memory
        for dimension_row in dimension_rows:
            dimension_guid, _, current_dimension_title, new_dimension_title = dimension_row
            print(f"-> {dimension_guid}")

            dimension_guids_to_new_titles[dimension_guid] = new_dimension_title

            try:
                dimension = Dimension.query.filter_by(guid=dimension_guid).one()
                measure_versions_to_dimension_guids[dimension.measure_version].append(dimension.guid)
                print(f"---> retrieved {dimension}")

            except NoResultFound:
                print(f"---> ERROR: No dimension found")
                error_count += 1
                continue

        print()
        print("2. VALIDATING DIMENSION TITLES CAN BE UPDATED")
        # Validate dimensions can be updated; record measures to skip if they fail validation
        for measure_version, dimension_guids in measure_versions_to_dimension_guids.items():
            print(f"-> {measure_version}")
            latest_measure_version = measure_version.measure.latest_version

            dimensions = [Dimension.query.get(dimension_guid) for dimension_guid in dimension_guids]
            unique_original_dimension_titles = set(d.title for d in dimensions)

            if not all(dimension_guids_to_new_titles[dimension.guid] for dimension in dimensions):
                skip_measures.add(measure_version)

            if len(dimensions) != len(unique_original_dimension_titles):
                print(f"---> ERROR: Measure {measure_version} contains dimensions with the same title; cannot process")
                skip_measures.add(measure_version)
                error_count += 1
                continue

            if measure_version is latest_measure_version:
                # No further validation required
                pass

            else:
                later_minor_measure_versions = list(
                    filter(
                        lambda mv: mv.major() == measure_version.major() and mv > measure_version,
                        measure_version.measure.versions,
                    )
                )
                if any(
                    later_minor_measure_version.external_edit_summary == STANDARD_EDIT_SUMMARY
                    for later_minor_measure_version in later_minor_measure_versions
                ):
                    skip_measures.add(measure_version)
                    continue

                if measure_version.major() < latest_measure_version.major():
                    pass

                else:
                    unique_latest_dimension_titles = set(d.title for d in latest_measure_version.dimensions)
                    if unique_original_dimension_titles != unique_latest_dimension_titles:
                        print(
                            f"---> ERROR: Dimension title mismatch between source {measure_version} and "
                            f"latest {latest_measure_version}."
                        )
                        print(f"---> Original titles {measure_version.version}: {[d.title for d in dimensions]}")
                        print(
                            f"--->      New titles {latest_measure_version.version}: "
                            f"{[d.title for d in latest_measure_version.dimensions]}"
                        )
                        skip_measures.add(measure_version)
                        error_count += 1
                        continue

                    if latest_measure_version.status in ("REJECTED", "INTERNAL_REVIEW", "DRAFT", "DEPARTMENT_REVIEW"):
                        print(
                            f"---> ERROR: Need latest measure version to be PUBLISHED; "
                            f"state is {latest_measure_version.status}."
                        )
                        print(f"---> Original version {measure_version.version}")
                        print(f"--->      New version {latest_measure_version.version}")
                        skip_measures.add(measure_version)
                        error_count += 1

        print()
        print("3. CREATING NEW MEASURE VERSIONS AND UPDATING DIMENSION TITLES")
        # Actually update the dimensions by creating a new measure and changing the titles
        for measure_version, dimension_guids in measure_versions_to_dimension_guids.items():
            print(f"-> {measure_version}")
            latest_measure_version = measure_version.measure.latest_version
            draft_measure_to_update = None

            if measure_version in skip_measures:
                print(f"---> SKIP")

            elif measure_version.major() < latest_measure_version.major():
                draft_measure_to_update = page_service.create_measure_version(
                    measure_version, NewVersionType.MINOR_UPDATE, user
                )

                print(f"---> Created draft {draft_measure_to_update}")

            else:
                if latest_measure_version.status == "APPROVED":
                    draft_measure_to_update = page_service.create_measure_version(
                        latest_measure_version, NewVersionType.MINOR_UPDATE, user
                    )

                    print(f"---> Created draft {draft_measure_to_update}")

                else:
                    raise RuntimeError("Unexpected status on measure_version")

            if draft_measure_to_update:
                draft_measure_to_update.update_corrects_data_mistake = False
                draft_measure_to_update.external_edit_summary = STANDARD_EDIT_SUMMARY

                dimensions = [Dimension.query.get(dimension_guid) for dimension_guid in dimension_guids]
                for dimension in dimensions:
                    for draft_dimension in draft_measure_to_update.dimensions:
                        if dimension.title == draft_dimension.title:
                            draft_dimension.title = dimension_guids_to_new_titles[dimension.guid]
                            print(
                                f"-----> Updated dimension {draft_dimension.guid} title from "
                                f"‘{dimension.title}’ to ‘{draft_dimension.title}’"
                            )
                            break
                    else:
                        raise RuntimeError(
                            f"Could not find dimension for measure_version={measure_version}, "
                            f"dimension={dimension}, dimension_title={dimension.title}"
                        )

                # From draft to internal review
                page_service.move_measure_version_to_next_state(draft_measure_to_update, updated_by=user_email)

                # From internal review to department review
                page_service.move_measure_version_to_next_state(draft_measure_to_update, updated_by=user_email)

                # From department review to approved
                page_service.move_measure_version_to_next_state(draft_measure_to_update, updated_by=user_email)

        db.session.commit()

        if error_count > 0:
            print(f"\n\n\nERRORS: {error_count}")

        return error_count


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("email", type=str, help="Email address of the user to attribute these updates to")
    parser.add_argument("dimension_csv", type=str, help="")
    args = parser.parse_args()

    dev_app = create_app(DevConfig)

    _dimension_rows = []
    with open(args.dimension_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        for row in csv_reader:
            _dimension_rows.append(row)

    # Remove header row
    _dimension_rows = _dimension_rows[1:]

    import_dimension_titles(user_email=args.email, app=dev_app, dimension_rows=_dimension_rows)

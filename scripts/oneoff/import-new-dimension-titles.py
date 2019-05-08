#!/usr/bin/env python


import sys
import csv
from argparse import ArgumentParser

sys.path.insert(0, ".")  # noqa



from datetime import datetime

from application.config import DevConfig
from application import db
from application.factory import create_app

from application.auth.models import User
from application.cms.models import Dimension
from application.cms.models import Dimension
from application.cms.page_service import PageService
from application.utils import create_guid
from sqlalchemy.orm.exc import NoResultFound


app = create_app(DevConfig)
with app.app_context():

  ap = ArgumentParser()
  ap.add_argument('email_address', help='email address for the user who will be attributed to updating the measure versions')
  args = ap.parse_args()

  user = User.query.filter_by(email=args.email_address).one()

  with open("dimension_titles.csv") as csv_file:

    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            dimension_guid = row[0]
            new_dimension_title = row[3]

            dimension = Dimension.query.filter_by(guid=dimension_guid).one()
            measure_version = dimension.measure_version
            measure = measure_version.measure

            latest_measure_version = measure.latest_version

            draft_measure_to_update = None

            if latest_measure_version.id == measure_version.id:

                draft_measure_to_update = create_measure_version(measure_version, NewVersionType.MINOR_UPDATE, user)
                draft_measure_to_update.external_edit_summary = "Updated dimension titles"


            else:
                if (latest_measure_version.status == "DRAFT"):
                    draft_measure_to_update = latest_measure_version
                else:
                    print(measure_version.title + " is in " + latest_measure_version.status)


            if draft_measure_to_update:

                try:
                    draft_dimension = Dimension.query.filter_by(measure_version_id=draft_measure_to_update.id, title=dimension.title).one()

                    if draft_dimension.title != new_dimension_title:
                        print("Updating '" + draft_dimension.title + "' to '" + new_dimension_title)

                        draft_dimension.title = new_dimension_title
                        db.session.add(draft_dimension)

                except NoResultFound:
                    print("Can't find dimension for " + dimension.title)

    db.session.commit()


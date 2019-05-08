#!/usr/bin/env python


import sys
import csv

sys.path.insert(0, ".")  # noqa


from datetime import datetime

from application.config import DevConfig
from application import db
from application.factory import create_app

from application.cms.models import Dimension
from application.cms.models import NewVersionType
from application.utils import create_guid
from sqlalchemy.orm.exc import NoResultFound

app = create_app(DevConfig)
with app.app_context():

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

            if (latest_measure_version.id == measure_version.id):

                print("creating DRAFT for " + measure_version.title)

                draft_measure_to_update = measure_version.copy()
                draft_measure_to_update.version = measure_version.next_version_number_by_type(NewVersionType.MINOR_UPDATE)

                draft_measure_to_update.status = "DRAFT"
                draft_measure_to_update.created_at = datetime.utcnow()
                draft_measure_to_update.published_at = None
                draft_measure_to_update.internal_edit_summary = None
                draft_measure_to_update.external_edit_summary = "Updated dimension titles"

                measure.versions.insert(0, draft_measure_to_update)

                draft_measure_to_update.dimensions = [dimension.copy() for dimension in measure_version.dimensions]
                draft_measure_to_update.data_sources = [data_source.copy() for data_source in measure_version.data_sources]
                draft_measure_to_update.latest = True

                draft_measure_to_update.uploads = []

                for upload in measure_version.uploads:
                    new_upload = upload.copy()
                    new_upload.guid = create_guid(upload.file_name)
                    draft_measure_to_update.uploads.append(new_upload)


                db.session.add(draft_measure_to_update)
                db.session.flush()



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
                        db.session.commit()

                except NoResultFound:
                    print("Can't find dimension for " + dimension.title)



import json
from datetime import datetime
from bidict import bidict
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import (
    CannotPublishRejected,
    AlreadyApproved,
    RejectionImpossible,
    DimensionNotFoundException,
    UploadNotFoundException)

from application import db

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    APPROVED=4,
    UNPUBLISHED=5
)


class DbPage(db.Model):
    __tablename__ = 'db_page'

    guid = db.Column(db.String(255), primary_key=True)
    uri = db.Column(db.String(255))
    description = db.Column(db.Text)
    page_type = db.Column(db.String(255))
    status = db.Column(db.String(255))
    publication_date = db.Column(db.Date)
    published = db.Column(db.BOOLEAN, default=False)

    parent_guid = db.Column(db.String(255), ForeignKey('db_page.guid'))
    children = relation('DbPage')

    uploads = db.relationship('DbUpload', backref='measure', lazy='dynamic')
    dimensions = db.relationship('DbDimension',
                                 backref='measure',
                                 lazy='dynamic',
                                 order_by='DbDimension.position')

    page_json = db.Column(JSON)
    measure_summary = db.Column(db.TEXT)
    summary = db.Column(db.TEXT)
    geographic_coverage = db.Column(db.TEXT)
    lowest_level_of_geography = db.Column(db.TEXT)
    time_covered = db.Column(db.String(255))
    need_to_know = db.Column(db.TEXT)
    ethnicity_definition_summary = db.Column(db.TEXT)
    ethnicity_definition_detail = db.Column(db.TEXT)
    source_text = db.Column(db.TEXT)
    source_url = db.Column(db.TEXT)
    department_source = db.Column(db.TEXT)
    published_date = db.Column(db.String(255))
    last_update_date = db.Column(db.String(255))
    next_update_date = db.Column(db.String(255))
    frequency = db.Column(db.String(255))
    related_publications = db.Column(db.TEXT)
    contact_name = db.Column(db.String(255))
    contact_phone = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    data_source_purpose = db.Column(db.TEXT)
    methodology = db.Column(db.TEXT)
    data_type = db.Column(db.String(255))
    suppression_rules = db.Column(db.TEXT)
    disclosure_control = db.Column(db.TEXT)
    estimation = db.Column(db.TEXT)
    type_of_statistic = db.Column(db.String(255))
    qmi_url = db.Column(db.TEXT)
    further_technical_information = db.Column(db.TEXT)
    title = db.Column(db.String(255))
    subtopics = db.Column(ARRAY(db.String))

    def get_dimension(self, guid):
        try:
            dimension = DbDimension.query.filter_by(guid=guid, measure=self).one()
            return dimension
        except NoResultFound as e:
            raise DimensionNotFoundException

    def get_upload(self, guid):
        try:
            upload = DbUpload.query.filter_by(guid=guid, measure=self).one()
            return upload
        except NoResultFound as e:
            raise UploadNotFoundException

    def publish_status(self, numerical=False):
        current_status = self.status.upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    def page_dict(self):
        return json.loads(self.page_json)

    def available_actions(self):

        if self.status == 'DRAFT':
            return ['APPROVE', 'UPDATE']

        if self.status == 'INTERNAL_REVIEW':
            return ['APPROVE', 'REJECT']

        if self.status == 'DEPARTMENT_REVIEW':
            return ['APPROVE', 'REJECT']

        if self.status == 'APPROVED':
            return ['UNPUBLISH']

        if self.status == 'REJECTED':
            return ['UPDATE']

        if self.status == 'UNPUBLISHED':
            return ['UPDATE']

    def next_state(self):
        num_status = self.publish_status(numerical=True)
        if num_status == 0:
            # You can only get out of rejected state by saving
            message = 'Page "{}" id: {} is rejected.'.format(self.title, self.guid)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status+1]
            self.status = new_status
            return 'Sent page "{}" id: {} to {}'.format(self.title, self.guid, new_status)
        else:
            message = 'Page "{}" id: {} is already approved'.format(self.title, self.guid)
            raise AlreadyApproved(message)

    def reject(self):
        if self.status == 'APPROVED':
            message = 'Page "{}" id: {} cannot be rejected in state {}'.format(self.title, self.guid, self.status)
            raise RejectionImpossible(message)

        rejected_state = 'REJECTED'
        message = 'Sent page "{}" id: {} to {}'.format(self.title, self.guid, rejected_state)
        self.status = rejected_state
        return message

    def unpublish(self):
        unpublished_state = publish_status.inv[5]
        message = 'Unpublished page "{}" id: {} - page will be removed from site'.format(self.title, self.guid)
        self.status = unpublished_state
        return message

    def not_editable(self):
        if self.publish_status(numerical=True) == 5:
            return False
        else:
            return self.publish_status(numerical=True) >= 2

    def eligible_for_build(self, beta_publication_states):
        if self.status in beta_publication_states and self.publication_date:
            return self.publication_date <= datetime.now().date()
        else:
            return self.status in beta_publication_states

    def to_dict(self):
        return {'guid': self.guid,
                'title': self.title}



class DbDimension(db.Model):

    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    time_period = db.Column(db.String(255))
    summary = db.Column(db.Text())
    suppression_rules = db.Column(db.Text())
    disclosure_control = db.Column(db.Text())
    type_of_statistic = db.Column(db.String(255))
    location = db.Column(db.String(255))
    source = db.Column(db.String(255))
    chart = db.Column(JSON)
    table = db.Column(JSON)
    chart_source_data = db.Column(JSON)
    table_source_data = db.Column(JSON)

    measure_id = db.Column(db.String(255), db.ForeignKey('db_page.guid'))

    position = db.Column(db.Integer)

    def to_dict(self):

        return {'guid': self.guid,
                'title': self.title,
                'measure': self.measure.guid,
                'time_period': self.time_period,
                'summary': self.summary,
                'suppression_rules': self.suppression_rules,
                'disclosure_control': self.disclosure_control,
                'type_of_statistic': self.type_of_statistic,
                'location': self.location,
                'source': self.source,
                'chart': self.chart,
                'table': self.table,
                'chart_source_data': self.chart_source_data,
                'table_source_data': self.table_source_data
                }


class DbUpload(db.Model):
    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    description = db.Column(db.Text())
    page_id = db.Column(db.String(255), db.ForeignKey('db_page.guid'))
    size = db.Column(db.String(255))

    def extension(self):
        return self.file_name.split('.')[-1]

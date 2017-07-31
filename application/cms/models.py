from datetime import datetime
from functools import total_ordering

from bidict import bidict
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
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


@total_ordering
class DbPage(db.Model):

    __tablename__ = 'db_page'

    def __eq__(self, other):
        return self.guid == other.guid and self.version == other.version

    def __hash__(self):
        return hash((self.guid, self.version))

    def __lt__(self, other):
        if self.major() <= other.major() and self.minor() < other.minor():
            return True
        else:
            return False

    guid = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(), nullable=False)

    uri = db.Column(db.String(255))
    description = db.Column(db.Text)
    page_type = db.Column(db.String(255))
    status = db.Column(db.String(255))
    publication_date = db.Column(db.Date)
    published = db.Column(db.BOOLEAN, default=False)

    parent_guid = db.Column(db.String(255))
    parent_version = db.Column(db.String())

    __table_args__ = (
        PrimaryKeyConstraint('guid', 'version', name='db_page_guid_version_pk'),
        ForeignKeyConstraint([parent_guid, parent_version],
                             ['db_page.guid', 'db_page.version']),
        {})

    children = relation('DbPage', lazy='dynamic')

    uploads = db.relationship('DbUpload', backref='measure', lazy='dynamic', cascade='all,delete')
    dimensions = db.relationship('DbDimension',
                                 backref='measure',
                                 lazy='dynamic',
                                 order_by='DbDimension.position',
                                 cascade='all,delete')

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime)

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

    def major(self):
        return int(self.version.split('.')[0])

    def minor(self):
        return int(self.version.split('.')[1])

    def next_minor_version(self):
        return '%s.%s' % (self.major(), self.minor() + 1)

    def get_latest_measures(self):
        if not self.children:
            return []
        latest = []
        seen = set([])
        for measure in self.children:
            if measure.guid not in seen and measure.is_latest():
                latest.append(measure)
                seen.add(measure.guid)
        return latest

    def number_of_versions(self):
        return len(self.get_versions())

    def has_minor_update(self):
        return len(self.minor_updates()) > 0

    def has_major_update(self):
        return len(self.major_updates()) > 0

    def is_latest(self):
        return not self.has_major_update() and not self.has_minor_update()

    def get_versions(self):
        return self.query.filter(DbPage.guid == self.guid).all()

    def has_no_later_published_versions(self, publication_states):
        updates = self.minor_updates() + self.major_updates()
        published = [page for page in updates if page.status in publication_states]
        return len(published) == 0

    def minor_updates(self):
        versions = DbPage.query.filter(DbPage.guid == self.guid, DbPage.version != self.version)
        return [page for page in versions if page.major() == self.major() and page.minor() > self.minor()]

    def major_updates(self):
        versions = DbPage.query.filter(DbPage.guid == self.guid, DbPage.version != self.version)
        return [page for page in versions if page.major() > self.major()]

    def to_dict(self):
        page_dict = {
            'guid': self.guid,
            'title': self.title,
            'measure_summary': self.measure_summary,
            'summary': self.summary,
            'geographic_coverage': self.geographic_coverage,
            'lowest_level_of_geography': self.lowest_level_of_geography,
            'time_covered': self.time_covered,
            'need_to_know': self.need_to_know,
            'ethnicity_definition_summary': self.ethnicity_definition_summary,
            'ethnicity_definition_detail': self.ethnicity_definition_detail,
            'source_text': self.source_text,
            'source_url': self.source_url,
            'department_source': self.department_source,
            'published_date': self.published_date,
            'last_update_date': self.last_update_date,
            'next_update_date': self.next_update_date,
            'frequency': self.frequency,
            'related_publications': self.related_publications,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'data_source_purpose': self.data_source_purpose,
            'methodology': self.methodology,
            'data_type': self.data_type,
            'suppression_rules': self.suppression_rules,
            'disclosure_control': self.disclosure_control,
            'estimation': self.estimation,
            'type_of_statistic': self.type_of_statistic,
            'qmi_url': self.qmi_url,
            'further_technical_information': self.further_technical_information,
            'dimensions': []
        }
        for dimension in self.dimensions:
            page_dict['dimensions'].append(dimension.to_dict())

        return page_dict


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

    measure_id = db.Column(db.String(255), nullable=False)
    measure_version = db.Column(db.String(), nullable=False)

    __table_args__ = (ForeignKeyConstraint([measure_id, measure_version], [DbPage.guid, DbPage.version]), {})

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

    page_id = db.Column(db.String(255), nullable=False)
    page_version = db.Column(db.String(), nullable=False)

    __table_args__ = (ForeignKeyConstraint([page_id, page_version], [DbPage.guid, DbPage.version]), {})

    def extension(self):
        return self.file_name.split('.')[-1]

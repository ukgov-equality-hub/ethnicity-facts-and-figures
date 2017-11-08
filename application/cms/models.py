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
    UNPUBLISH=5,
    UNPUBLISHED=6
)


@total_ordering
class DbPage(db.Model):

    __tablename__ = 'db_page'

    def __eq__(self, other):
        return self.guid == other.guid and self.version == other.version

    def __hash__(self):
        return hash((self.guid, self.version))

    def __lt__(self, other):
        if self.major() < other.major():
            return True
        elif self.major() == other.major() and self.minor() < other.minor():
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

    db_version_id = db.Column(db.Integer, nullable=False)
    __mapper_args__ = {
        "version_id_col": db_version_id
    }

    children = relation('DbPage', lazy='dynamic', order_by='DbPage.position')

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
    related_publications = db.Column(db.TEXT)
    data_source_purpose = db.Column(db.TEXT)
    methodology = db.Column(db.TEXT)
    data_type = db.Column(db.String(255))
    estimation = db.Column(db.TEXT)
    qmi_url = db.Column(db.TEXT)
    further_technical_information = db.Column(db.TEXT)
    title = db.Column(db.String(255))
    subtopics = db.Column(ARRAY(db.String))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime)
    external_edit_summary = db.Column(db.TEXT)
    internal_edit_summary = db.Column(db.TEXT)

    # Primary Source
    # TODO: rename these to be consistant with secondary sources.
    source_text = db.Column(db.TEXT)
    department_source = db.Column(db.TEXT)
    source_url = db.Column(db.TEXT)
    published_date = db.Column(db.String(255))
    last_update_date = db.Column(db.String(255))
    next_update_date = db.Column(db.String(255))
    frequency = db.Column(db.String(255))
    type_of_statistic = db.Column(db.String(255))
    suppression_rules = db.Column(db.TEXT)
    disclosure_control = db.Column(db.TEXT)
    contact_name = db.Column(db.String(255))
    contact_phone = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))

    primary_source_contact_2_name = db.Column(db.TEXT)
    primary_source_contact_2_email = db.Column(db.TEXT)
    primary_source_contact_2_phone = db.Column(db.TEXT)

    # Secondary Source 1
    secondary_source_1_title = db.Column(db.TEXT)
    secondary_source_1_publisher = db.Column(db.TEXT)
    secondary_source_1_url = db.Column(db.TEXT)
    secondary_source_1_date = db.Column(db.TEXT)
    secondary_source_1_date_updated = db.Column(db.TEXT)
    secondary_source_1_date_next_update = db.Column(db.TEXT)
    secondary_source_1_frequency = db.Column(db.TEXT)
    secondary_source_1_statistic_type = db.Column(db.TEXT)
    secondary_source_1_suppression_rules = db.Column(db.TEXT)
    secondary_source_1_disclosure_control = db.Column(db.TEXT)
    secondary_source_1_contact_1_name = db.Column(db.TEXT)
    secondary_source_1_contact_1_email = db.Column(db.TEXT)
    secondary_source_1_contact_1_phone = db.Column(db.TEXT)
    secondary_source_1_contact_2_name = db.Column(db.TEXT)
    secondary_source_1_contact_2_email = db.Column(db.TEXT)
    secondary_source_1_contact_2_phone = db.Column(db.TEXT)

    # Secondary Source 2
    secondary_source_2_title = db.Column(db.TEXT)
    secondary_source_2_publisher = db.Column(db.TEXT)
    secondary_source_2_url = db.Column(db.TEXT)
    secondary_source_2_date = db.Column(db.TEXT)
    secondary_source_2_date_updated = db.Column(db.TEXT)
    secondary_source_2_date_next_update = db.Column(db.TEXT)
    secondary_source_2_frequency = db.Column(db.TEXT)
    secondary_source_2_statistic_type = db.Column(db.TEXT)
    secondary_source_2_suppression_rules = db.Column(db.TEXT)
    secondary_source_2_disclosure_control = db.Column(db.TEXT)
    secondary_source_2_contact_1_name = db.Column(db.TEXT)
    secondary_source_2_contact_1_email = db.Column(db.TEXT)
    secondary_source_2_contact_1_phone = db.Column(db.TEXT)
    secondary_source_2_contact_2_name = db.Column(db.TEXT)
    secondary_source_2_contact_2_email = db.Column(db.TEXT)
    secondary_source_2_contact_2_phone = db.Column(db.TEXT)

    position = db.Column(db.Integer, default=0)

    additional_description = db.Column(db.TEXT)

    created_by = db.Column(db.String(255))
    last_updated_by = db.Column(db.String(255))
    published_by = db.Column(db.String(255))
    unpublished_by = db.Column(db.String(255))

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

        if self.status in ['REJECTED', 'UNPUBLISHED']:
            return ['RETURN_TO_DRAFT']
        else:
            return []

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
        unpublish_state = publish_status.inv[5]
        message = 'Request to un-publish page "{}" id: {} - will be removed from site'.format(self.title, self.guid)
        self.status = unpublish_state
        return message

    def not_editable(self):
        if self.publish_status(numerical=True) == 5:
            return False
        else:
            return self.publish_status(numerical=True) >= 2

    def eligible_for_build(self, publication_states):
        return self.status in publication_states

    def major(self):
        return int(self.version.split('.')[0])

    def minor(self):
        return int(self.version.split('.')[1])

    def next_minor_version(self):
        return '%s.%s' % (self.major(), self.minor() + 1)

    def next_major_version(self):
        return '%s.0' % str(self.major() + 1)

    def next_version_number_by_type(self, version_type):
        if version_type == 'minor':
            return self.next_minor_version()
        return self.next_major_version()

    def latest_version(self):
        versions = self.get_versions()
        versions.sort(reverse=True)
        return versions[0] if versions else self

    def number_of_versions(self):
        return len(self.get_versions())

    def has_minor_update(self):
        return len(self.minor_updates()) > 0

    def has_major_update(self):
        return len(self.major_updates()) > 0

    def is_latest(self):
        return not self.has_major_update() and not self.has_minor_update()

    def is_minor_version(self):
        return self.minor() != 0

    def is_major_version(self):
        return not self.is_minor_version()

    def get_versions(self, include_self=True):
        if include_self:
            return self.query.filter(DbPage.guid == self.guid).all()
        else:
            return self.query.filter(DbPage.guid == self.guid, DbPage.version != self.version).all()

    def get_previous_version(self):
        versions = self.get_versions(include_self=False)
        versions.sort(reverse=True)
        return versions[0] if versions else None

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

    def parent(self):
        return DbPage.query.filter(DbPage.guid == self.parent_guid, DbPage.version == self.parent_version).first()

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

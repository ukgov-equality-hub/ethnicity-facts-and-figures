import enum
import re
from datetime import datetime, timedelta
from functools import total_ordering

import sqlalchemy
from bidict import bidict
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relation, relationship, backref
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.orm.exc import NoResultFound

from application.cms.exceptions import (
    CannotPublishRejected,
    AlreadyApproved,
    RejectionImpossible,
    DimensionNotFoundException,
    UploadNotFoundException
)

from application import db
from application.utils import get_token_age

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    APPROVED=4,
    UNPUBLISH=5,
    UNPUBLISHED=6
)


class TypeOfData(enum.Enum):
    ADMINISTRATIVE = 'Administrative'
    SURVEY = 'Survey (including census)'


class UKCountry(enum.Enum):
    ENGLAND = 'England'
    WALES = 'Wales'
    SCOTLAND = 'Scotland'
    NORTHERN_IRELAND = 'Northern Ireland'
    UK = 'UK'


class TypeOfOrganisation(enum.Enum):
    MINISTERIAL_DEPARTMENT = 'Ministerial department'
    NON_MINISTERIAL_DEPARTMENT = 'Non-ministerial department'
    EXECUTIVE_OFFICE = 'Executive office'
    EXECUTIVE_AGENCY = 'Executive agency'
    DEVOLVED_ADMINISTRATION = 'Devolved administration'
    COURT = 'Court'
    TRIBUNAL_NON_DEPARTMENTAL_PUBLIC_BODY = 'Tribunal non-departmental public body'
    CIVIL_SERVICE = 'Civil Service'
    EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY = 'Executive non-departmental public body'
    INDEPENDENT_MONITORING_BODY = 'Independent monitoring body'
    PUBLIC_CORPORATION = 'Public corporation'
    SUB_ORGANISATION = 'Sub-organisation'
    AD_HOC_ADVISORY_GROUP = 'Ad-hoc advisory group'
    ADVISORY_NON_DEPARTMENTAL_PUBLIC_BODY = 'Advisory non-departmental public body'
    OTHER = 'Other'

    def pluralise(self):

        if self == TypeOfOrganisation.CIVIL_SERVICE:
            return self.value

        if self == TypeOfOrganisation.EXECUTIVE_AGENCY:
            return self.value.replace('agency', 'agencies')

        if self in [TypeOfOrganisation.TRIBUNAL_NON_DEPARTMENTAL_PUBLIC_BODY,
                    TypeOfOrganisation.EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY,
                    TypeOfOrganisation.INDEPENDENT_MONITORING_BODY,
                    TypeOfOrganisation.ADVISORY_NON_DEPARTMENTAL_PUBLIC_BODY]:
            return self.value.replace('body', 'bodies')

        return '%ss' % self.value


# This is from  http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html#using-enum-with-array
class ArrayOfEnum(ARRAY):

    def bind_expression(self, bindvalue):
        return sqlalchemy.cast(bindvalue, self)

    def result_processor(self, dialect, coltype):
        super_rp = super(ArrayOfEnum, self).result_processor(
            dialect, coltype)

        def handle_raw_string(value):
            inner = re.match(r"^{(.*)}$", value).group(1)
            return inner.split(",") if inner else []

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))

        return process


class FrequencyOfRelease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)


class TypeOfStatistic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internal = db.Column(db.String(), nullable=False)
    external = db.Column(db.String(), nullable=False)
    position = db.Column(db.Integer, nullable=False)


@total_ordering
class Page(db.Model):

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
    internal_reference = db.Column(db.String())
    latest = db.Column(db.Boolean, default=True)

    uri = db.Column(db.String(255))
    description = db.Column(db.Text)
    page_type = db.Column(db.String(255))
    status = db.Column(db.String(255))
    publication_date = db.Column(db.Date)
    published = db.Column(db.BOOLEAN, default=False)

    parent_guid = db.Column(db.String(255))
    parent_version = db.Column(db.String())
    parent = relation('Page', remote_side=[guid, version], backref=backref('children', order_by='Page.position'))

    __table_args__ = (
        PrimaryKeyConstraint('guid', 'version', name='page_guid_version_pk'),
        ForeignKeyConstraint([parent_guid, parent_version],
                             ['page.guid', 'page.version']),
        UniqueConstraint('guid', 'version', name='uix_page_guid_version'),
        {})

    db_version_id = db.Column(db.Integer, nullable=False)
    __mapper_args__ = {
        "version_id_col": db_version_id
    }

    uploads = db.relationship('Upload', backref='page', lazy='dynamic', cascade='all,delete')
    dimensions = db.relationship('Dimension',
                                 backref='page',
                                 lazy='dynamic',
                                 order_by='Dimension.position',
                                 cascade='all,delete')

    measure_summary = db.Column(db.TEXT)
    summary = db.Column(db.TEXT)
    area_covered = db.Column(ArrayOfEnum(db.Enum(UKCountry, name='uk_country_types')), default=[])

    lowest_level_of_geography_id = db.Column(db.String(255),
                                             ForeignKey('lowest_level_of_geography.name'),
                                             nullable=True)
    lowest_level_of_geography = relationship('LowestLevelOfGeography', back_populates='pages')

    time_covered = db.Column(db.String(255))
    need_to_know = db.Column(db.TEXT)
    ethnicity_definition_summary = db.Column(db.TEXT)
    ethnicity_definition_detail = db.Column(db.TEXT)
    related_publications = db.Column(db.TEXT)
    methodology = db.Column(db.TEXT)

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
    type_of_data = db.Column(ArrayOfEnum(db.Enum(TypeOfData, name='type_of_data_types')), default=[])
    type_of_statistic_id = db.Column(db.Integer, ForeignKey('type_of_statistic.id'))
    type_of_statistic_description = relationship('TypeOfStatistic', foreign_keys=[type_of_statistic_id])
    department_source_text = db.Column(db.TEXT)
    department_source_id = db.Column(db.String(255), ForeignKey('organisation.id'), nullable=True)
    department_source = relationship('Organisation',
                                     foreign_keys=[department_source_id],
                                     back_populates='pages')
    source_url = db.Column(db.TEXT)
    published_date = db.Column(db.String(255))
    note_on_corrections_or_updates = db.Column(db.TEXT)
    frequency_id = db.Column(db.Integer, ForeignKey('frequency_of_release.id'))
    frequency_of_release = relationship('FrequencyOfRelease', foreign_keys=[frequency_id])
    frequency_other = db.Column(db.String(255))
    data_source_purpose = db.Column(db.TEXT)
    suppression_rules = db.Column(db.TEXT)
    disclosure_control = db.Column(db.TEXT)
    suppression_and_disclosure = db.Column(db.TEXT)
    estimation = db.Column(db.TEXT)

    # End primary Source

    # Secondary Source
    secondary_source_1_title = db.Column(db.TEXT)
    secondary_source_1_type_of_data = db.Column(ArrayOfEnum(db.Enum(TypeOfData, name='type_of_data_types')), default=[])
    secondary_source_1_statistic_type = db.Column(db.TEXT)
    secondary_source_1_publisher_text = db.Column(db.TEXT)
    secondary_source_1_publisher_id = db.Column(db.String(255),
                                                ForeignKey('organisation.id',
                                                           name='organisation_secondary_source_1_fkey'),
                                                nullable=True)
    secondary_source_1_publisher = relationship('Organisation',
                                                foreign_keys=[secondary_source_1_publisher_id])

    secondary_source_1_url = db.Column(db.TEXT)
    secondary_source_1_date = db.Column(db.TEXT)
    secondary_source_1_note_on_corrections_or_updates = db.Column(db.TEXT)
    secondary_source_1_frequency = db.Column(db.TEXT)
    secondary_source_1_frequency_id = db.Column(db.Integer, ForeignKey('frequency_of_release.id',
                                                                       name='frequency_secondary_source_1_fkey'))
    secondary_source_1_frequency_of_release = relationship('FrequencyOfRelease',
                                                           foreign_keys=[secondary_source_1_frequency_id])
    secondary_source_1_frequency_other = db.Column(db.String(255))
    secondary_source_1_data_source_purpose = db.Column(db.TEXT)

    secondary_source_1_type_of_statistic_id = db.Column(db.Integer, ForeignKey('type_of_statistic.id'))
    secondary_source_1_type_of_statistic_description = relationship('TypeOfStatistic',
                                                                    foreign_keys=[
                                                                        secondary_source_1_type_of_statistic_id])  # noqa
    # End secondary Source

    contact_name = db.Column(db.TEXT)
    contact_phone = db.Column(db.TEXT)
    contact_email = db.Column(db.TEXT)

    contact_2_name = db.Column(db.TEXT)
    contact_2_phone = db.Column(db.TEXT)
    contact_2_email = db.Column(db.TEXT)

    position = db.Column(db.Integer, default=0)

    additional_description = db.Column(db.TEXT)

    created_by = db.Column(db.String(255))
    last_updated_by = db.Column(db.String(255))
    published_by = db.Column(db.String(255))
    unpublished_by = db.Column(db.String(255))
    review_token = db.Column(db.String())

    def get_dimension(self, guid):
        try:
            dimension = Dimension.query.filter_by(guid=guid, page=self).one()
            return dimension
        except NoResultFound as e:
            raise DimensionNotFoundException

    def get_upload(self, guid):
        try:
            upload = Upload.query.filter_by(guid=guid).one()
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

        if self.parent.parent.guid == 'topic_testingspace':
            return ['UPDATE']
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
            message = 'Page "{}" is rejected.'.format(self.title)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status + 1]
            self.status = new_status
            return 'Sent page "{}" to {}'.format(self.title, new_status)
        else:
            message = 'Page "{}" is already approved'.format(self.title)
            raise AlreadyApproved(message)

    def reject(self):
        if self.status == 'APPROVED':
            message = 'Page "{}" cannot be rejected in state {}'.format(self.title, self.status)
            raise RejectionImpossible(message)

        rejected_state = 'REJECTED'
        message = 'Sent page "{}" to {}'.format(self.title, rejected_state)
        self.status = rejected_state
        return message

    def unpublish(self):
        unpublish_state = publish_status.inv[5]
        message = 'Request to un-publish page "{}" - page will be removed from site'.format(self.title)
        self.status = unpublish_state
        return message

    def not_editable(self):
        if self.publish_status(numerical=True) == 5:
            return False
        else:
            return self.publish_status(numerical=True) >= 2

    def eligible_for_build(self):
        return self.status == 'APPROVED'

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

    def is_minor_version(self):
        return self.minor() != 0

    def is_major_version(self):
        return not self.is_minor_version()

    def get_versions(self, include_self=True):
        if include_self:
            return self.query.filter(Page.guid == self.guid).all()
        else:
            return self.query.filter(Page.guid == self.guid, Page.version != self.version).all()

    def get_previous_version(self):
        versions = self.get_versions(include_self=False)
        versions.sort(reverse=True)
        return versions[0] if versions else None

    def has_no_later_published_versions(self):
        updates = self.minor_updates() + self.major_updates()
        published = [page for page in updates if page.status == 'APPROVED']
        return len(published) == 0

    def minor_updates(self):
        versions = Page.query.filter(Page.guid == self.guid, Page.version != self.version)
        return [page for page in versions if page.major() == self.major() and page.minor() > self.minor()]

    def major_updates(self):
        versions = Page.query.filter(Page.guid == self.guid, Page.version != self.version)
        return [page for page in versions if page.major() > self.major()]

    def format_area_covered(self):
        if self.area_covered is None:
            return ''
        if len(self.area_covered) == 0:
            return ''
        if len(self.area_covered) == 1:
            return self.area_covered[0].value
        else:
            last = self.area_covered[-1]
            first = self.area_covered[:-1]
            comma_separated = ', '.join([item.value for item in first])
            return '%s and %s' % (comma_separated, last.value)

    def to_dict(self, with_dimensions=False):
        page_dict = {
            'guid': self.guid,
            'title': self.title,
            'measure_summary': self.measure_summary,
            'summary': self.summary,
            'area_covered': self.area_covered,
            'lowest_level_of_geography': self.lowest_level_of_geography,
            'time_covered': self.time_covered,
            'need_to_know': self.need_to_know,
            'ethnicity_definition_summary': self.ethnicity_definition_summary,
            'ethnicity_definition_detail': self.ethnicity_definition_detail,
            'source_text': self.source_text,
            'source_url': self.source_url,
            'department_source': self.department_source,
            'published_date': self.published_date,
            'frequency': self.frequency_of_release.description if self.frequency_of_release else None,
            'related_publications': self.related_publications,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'data_source_purpose': self.data_source_purpose,
            'methodology': self.methodology,
            'type_of_data': [t.name for t in self.type_of_data] if self.type_of_data else None,
            'suppression_rules': self.suppression_rules,
            'disclosure_control': self.disclosure_control,
            'estimation': self.estimation,
            'type_of_statistic':
                self.type_of_statistic_description.external if self.type_of_statistic_description else None,
            'qmi_url': self.qmi_url,
            'further_technical_information': self.further_technical_information,
        }

        if with_dimensions:
            page_dict['dimensions'] = []
            for dimension in self.dimensions:
                page_dict['dimensions'].append(dimension.to_dict())

        return page_dict

    def review_token_expires_in(self, config):
        try:
            token_age = get_token_age(self.review_token, config)
            max_token_age_days = config.get('PREVIEW_TOKEN_MAX_AGE_DAYS')
            expiry = token_age + timedelta(days=max_token_age_days)
            days_from_now = expiry.date() - datetime.today().date()
            return days_from_now.days
        except Exception:
            return 0


class Dimension(db.Model):
    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    time_period = db.Column(db.String(255))
    summary = db.Column(db.Text())

    chart = db.Column(JSON)
    table = db.Column(JSON)
    chart_source_data = db.Column(JSON)
    table_source_data = db.Column(JSON)

    page_id = db.Column(db.String(255), nullable=False)
    page_version = db.Column(db.String(), nullable=False)

    __table_args__ = (ForeignKeyConstraint([page_id, page_version], [Page.guid, Page.version]), {})

    position = db.Column(db.Integer)

    categorisation_links = db.relationship('DimensionCategorisation',
                                           backref='dimension',
                                           lazy='dynamic',
                                           cascade='all,delete')

    def to_dict(self):
        return {'guid': self.guid,
                'title': self.title,
                'measure': self.page.guid,
                'time_period': self.time_period,
                'summary': self.summary,
                'chart': self.chart,
                'table': self.table,
                'chart_source_data': self.chart_source_data,
                'table_source_data': self.table_source_data
                }


class Upload(db.Model):
    guid = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    description = db.Column(db.Text())
    size = db.Column(db.String(255))

    page_id = db.Column(db.String(255), nullable=False)
    page_version = db.Column(db.String(), nullable=False)

    __table_args__ = (ForeignKeyConstraint([page_id, page_version], [Page.guid, Page.version]), {})

    def extension(self):
        return self.file_name.split('.')[-1]


'''
  The categorisation models allow us to associate dimensions with lists of values

  This allows us to (for example)...
   1. find measures use the 2011 18+1 breakdown (a DimensionCategorisation)
   2. find measures or dimensions that have information on Gypsy/Roma
'''

association_table = db.Table('association', db.metadata,
                             db.Column('categorisation_id', db.Integer, ForeignKey('categorisation.id')),
                             db.Column('categorisation_value_id', db.Integer, ForeignKey('categorisation_value.id'))
                             )
parent_association_table = db.Table('parent_association', db.metadata,
                                    db.Column('categorisation_id', db.Integer, ForeignKey('categorisation.id')),
                                    db.Column('categorisation_value_id', db.Integer,
                                              ForeignKey('categorisation_value.id'))
                                    )


class Categorisation(db.Model):
    __tablename__ = 'categorisation'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255))
    title = db.Column(db.String(255))
    family = db.Column(db.String(255))
    subfamily = db.Column(db.String(255))
    position = db.Column(db.Integer)

    dimension_links = db.relationship('DimensionCategorisation',
                                      backref='categorisation',
                                      lazy='dynamic',
                                      cascade='all,delete')

    values = relationship("CategorisationValue", secondary=association_table, back_populates="categorisations")
    parent_values = relationship("CategorisationValue",
                                 secondary=parent_association_table,
                                 back_populates="categorisations_as_parent")

    def to_dict(self):
        return {'id': self.id,
                'title': self.title,
                'family': self.family,
                'subfamily': self.subfamily,
                'position': self.position,
                'values': [v.value for v in self.values]
                }


class CategorisationValue(db.Model):
    __tablename__ = 'categorisation_value'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(255))
    position = db.Column(db.Integer())

    categorisations = relationship("Categorisation", secondary=association_table, back_populates="values")
    categorisations_as_parent = relationship("Categorisation",
                                             secondary=parent_association_table,
                                             back_populates="parent_values")


class DimensionCategorisation(db.Model):
    __tablename__ = 'dimension_categorisation'

    dimension_guid = db.Column(db.String(255), primary_key=True)
    categorisation_id = db.Column(db.Integer, primary_key=True)

    includes_parents = db.Column(db.Boolean)
    includes_all = db.Column(db.Boolean)
    includes_unknown = db.Column(db.Boolean)

    __table_args__ = (ForeignKeyConstraint([dimension_guid], [Dimension.guid]),
                      ForeignKeyConstraint([categorisation_id], [Categorisation.id]), {})


class Organisation(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    other_names = db.Column(ARRAY(db.String), default=[])
    abbreviations = db.Column(ARRAY(db.String), default=[])
    organisation_type = db.Column(db.Enum(TypeOfOrganisation, name='type_of_organisation_types'), nullable=False)

    pages = relationship('Page', back_populates='department_source', foreign_keys=[Page.department_source_id])

    @classmethod
    def select_options_by_type(cls):
        organisations_by_type = []
        for org_type in TypeOfOrganisation:
            orgs = cls.query.filter_by(organisation_type=org_type).all()
            organisations_by_type.append((org_type, orgs))
        return organisations_by_type

    def abbreviations_data(self):
        return '|'.join(self.abbreviations)

    def other_names_data(self):
        return '|'.join(self.other_names)


class LowestLevelOfGeography(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    description = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, nullable=False)

    pages = relationship('Page', back_populates='lowest_level_of_geography')

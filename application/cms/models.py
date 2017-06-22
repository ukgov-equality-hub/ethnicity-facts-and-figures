import json
from datetime import datetime
from bidict import bidict
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.dialects.postgresql import JSON

from application.cms.exceptions import CannotPublishRejected, AlreadyApproved, RejectionImpossible, \
    DimensionNotFoundException
from application import db


publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    ACCEPTED=4
)


class DbPage(db.Model):

    __tablename__ = 'db_page'

    guid = db.Column(db.String(255), primary_key=True)
    uri = db.Column(db.String(255))
    description = db.Column(db.String(255))
    page_type = db.Column(db.String(255))
    status = db.Column(db.String(255))
    publication_date = db.Column(db.Date)

    parent_guid = db.Column(db.String(255), ForeignKey('db_page.guid'))
    children = relation('DbPage')

    page_json = db.Column(JSON)

    # def __getattr__(self, name):
    #     if name in self.page_dict():
    #         return self.page_dict()[name]
    #     else:
    #         raise AttributeError(name)

    @property
    def measure_summary(self):
        return self.page_dict()['measure_summary']

    @measure_summary.setter
    def measure_summary(self, measure_summary):
        d = self.page_dict()
        d['measure_summary'] = measure_summary
        self.page_json = json.dumps(d)

    @property
    def summary(self):
        return self.page_dict()['summary']

    @summary.setter
    def summary(self, summary):
        d = self.page_dict()
        d['summary'] = summary
        self.page_json = json.dumps(d)

    @property
    def geographic_coverage(self):
        return self.page_dict()['geographic_coverage']

    @geographic_coverage.setter
    def geographic_coverage(self, geographic_coverage):
        d = self.page_dict()
        d['geographic_coverage'] = geographic_coverage
        self.page_json = json.dumps(d)

    @property
    def lowest_level_of_geography(self):
        return self.page_dict()['lowest_level_of_geography']

    @lowest_level_of_geography.setter
    def lowest_level_of_geography(self, lowest_level_of_geography):
        d = self.page_dict()
        d['lowest_level_of_geography'] = lowest_level_of_geography
        self.page_json = json.dumps(d)

    @property
    def time_covered(self):
        return self.page_dict()['time_covered']

    @time_covered.setter
    def time_covered(self, time_covered):
        d = self.page_dict()
        d['time_covered'] = time_covered
        self.page_json = json.dumps(d)

    @property
    def need_to_know(self):
        return self.page_dict()['need_to_know']

    @need_to_know.setter
    def need_to_know(self, need_to_know):
        d = self.page_dict()
        d['need_to_know'] = need_to_know
        self.page_json = json.dumps(d)

    @property
    def ethnicity_definition_summary(self):
        return self.page_dict()['ethnicity_definition_summary']

    @ethnicity_definition_summary.setter
    def ethnicity_definition_summary(self, ethnicity_definition_summary):
        d = self.page_dict()
        d['ethnicity_definition_summary'] = ethnicity_definition_summary
        self.page_json = json.dumps(d)

    @property
    def ethnicity_definition_detail(self):
        return self.page_dict()['ethnicity_definition_detail']

    @ethnicity_definition_detail.setter
    def ethnicity_definition_detail(self, ethnicity_definition_detail):
        d = self.page_dict()
        d['ethnicity_definition_detail'] = ethnicity_definition_detail
        self.page_json = json.dumps(d)

    @property
    def source_text(self):
        return self.page_dict()['source_text']

    @source_text.setter
    def source_text(self, source_text):
        d = self.page_dict()
        d['source_text'] = source_text
        self.page_json = json.dumps(d)

    @property
    def source_url(self):
        return self.page_dict()['source_url']

    @source_url.setter
    def source_url(self, source_url):
        d = self.page_dict()
        d['source_url'] = source_url
        self.page_json = json.dumps(d)

    @property
    def department_source(self):
        return self.page_dict()['department_source']

    @department_source.setter
    def department_source(self, department_source):
        d = self.page_dict()
        d['department_source'] = department_source
        self.page_json = json.dumps(d)

    @property
    def published_date(self):
        return self.page_dict()['published_date']

    @published_date.setter
    def published_date(self, published_date):
        d = self.page_dict()
        d['published_date'] = published_date
        self.page_json = json.dumps(d)

    @property
    def last_update_date(self):
        return self.page_dict()['last_update_date']

    @published_date.setter
    def last_update_date(self, last_update_date):
        d = self.page_dict()
        d['last_update_date'] = last_update_date
        self.page_json = json.dumps(d)

    @property
    def next_update_date(self):
        return self.page_dict()['next_update_date']

    @next_update_date.setter
    def last_update_date(self, next_update_date):
        d = self.page_dict()
        d['next_update_date'] = next_update_date
        self.page_json = json.dumps(d)

    @property
    def frequency(self):
        return self.page_dict()['frequency']

    @frequency.setter
    def frequency(self, frequency):
        d = self.page_dict()
        d['frequency'] = frequency
        self.page_json = json.dumps(d)

    @property
    def related_publications(self):
        return self.page_dict()['related_publications']

    @related_publications.setter
    def related_publications(self, related_publications):
        d = self.page_dict()
        d['related_publications'] = related_publications
        self.page_json = json.dumps(d)

    @property
    def contact_name(self):
        return self.page_dict()['contact_name']

    @contact_name.setter
    def contact_name(self, contact_name):
        d = self.page_dict()
        d['contact_name'] = contact_name
        self.page_json = json.dumps(d)

    @property
    def contact_phone(self):
        return self.page_dict()['contact_phone']

    @contact_phone.setter
    def contact_phone(self, contact_phone):
        d = self.page_dict()
        d['contact_phone'] = contact_phone
        self.page_json = json.dumps(d)

    @property
    def contact_email(self):
        return self.page_dict()['contact_email']

    @contact_email.setter
    def contact_email(self, contact_email):
        d = self.page_dict()
        d['contact_email'] = contact_email
        self.page_json = json.dumps(d)

    @property
    def data_source_purpose(self):
        return self.page_dict()['data_source_purpose']

    @data_source_purpose.setter
    def data_source_purpose(self, data_source_purpose):
        d = self.page_dict()
        d['data_source_purpose'] = data_source_purpose
        self.page_json = json.dumps(d)

    @property
    def methodology(self):
        return self.page_dict()['methodology']

    @methodology.setter
    def methodology(self, methodology):
        d = self.page_dict()
        d['methodology'] = methodology
        self.page_json = json.dumps(d)

    @property
    def data_type(self):
        return self.page_dict()['data_type']

    @data_type.setter
    def data_type(self, data_type):
        d = self.page_dict()
        d['data_type'] = data_type
        self.page_json = json.dumps(d)

    @property
    def suppression_rules(self):
        return self.page_dict()['suppression_rules']

    @suppression_rules.setter
    def suppression_rules(self, suppression_rules):
        d = self.page_dict()
        d['suppression_rules'] = suppression_rules
        self.page_json = json.dumps(d)

    @property
    def disclosure_control(self):
        return self.page_dict()['disclosure_control']

    @disclosure_control.setter
    def disclosure_control(self, disclosure_control):
        d = self.page_dict()
        d['disclosure_control'] = disclosure_control
        self.page_json = json.dumps(d)

    @property
    def estimation(self):
        return self.page_dict()['estimation']

    @estimation.setter
    def estimation(self, estimation):
        d = self.page_dict()
        d['estimation'] = estimation
        self.page_json = json.dumps(d)

    @property
    def type_of_statistic(self):
        return self.page_dict()['type_of_statistic']

    @type_of_statistic.setter
    def type_of_statistic(self, type_of_statistic):
        d = self.page_dict()
        d['type_of_statistic'] = type_of_statistic
        self.page_json = json.dumps(d)

    @property
    def qmi_url(self):
        return self.page_dict()['qmi_url']

    @qmi_url.setter
    def qmi_url(self, qmi_url):
        d = self.page_dict()
        d['qmi_url'] = qmi_url
        self.page_json = json.dumps(d)

    @property
    def further_technical_information(self):
        return self.page_dict()['further_technical_information']

    @further_technical_information.setter
    def further_technical_information(self, further_technical_information):
        d = self.page_dict()
        d['further_technical_information'] = further_technical_information
        self.page_json = json.dumps(d)

    @property
    def subtopics(self):
        return self.page_dict()['subtopics']

    @subtopics.setter
    def subtopics(self, subtopics):
        d = self.page_dict()
        d['subtopics'] = subtopics
        self.page_json = json.dumps(d)

    @property
    def title(self):
        return self.page_dict()['title']

    @title.setter
    def title(self, title):
        d = self.page_dict()
        d['title'] = title
        self.page_json = json.dumps(d)

    @property
    def type_of_statistic(self):
        return self.page_dict()['type_of_statistic']

    @type_of_statistic.setter
    def type_of_statistic(self, type_of_statistic):
        d = self.page_dict()
        d['type_of_statistic'] = type_of_statistic
        self.page_json = json.dumps(d)

    @property
    def dimensions(self):
        return self.page_dict().get('dimensions', [])

    @dimensions.setter
    def dimensions(self, dimensions):
        d = self.page_dict()
        d['dimensions'] = dimensions
        self.page_json = json.dumps(d)

    def add_dimension(self, dimension):
        if not self.dimensions:
            d = {'dimensions': [dimension.__dict__()]}
            new_page = {**self.page_dict(), **d}
            self.page_json = json.dumps(new_page)
        else:
            dimensions = self.page_dict()['dimensions']
            dimensions.append(dimension.__dict__())
            self.dimensions = dimensions

    def get_dimension(self, guid):
        filtered = [d for d in self.dimensions if d['guid'] == guid]
        if len(filtered) == 0:
            raise DimensionNotFoundException
        else:
            d = filtered[0]
            return Dimension(**d)

    def update_dimension(self, dimension):
        others = [d for d in self.dimensions if d['guid'] != dimension.guid]
        others.append(dimension.__dict__())
        self.dimensions = others

    def to_dict(self):
        return {'uri': self.uri,
                'parent': self.parent_guid,
                'page_type': self.page_type,
                'status': self.status,
                'guid': self.guid,
                'publication_date': self.publication_date}

    def publish_status(self, numerical=False):
        current_status = self.status.upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    def page_dict(self):
        return json.loads(self.page_json)

    def available_actions(self):
        """Returns the states available for this page -- WIP"""
        num_status = self.publish_status(numerical=True)
        states = []
        if num_status == 4:  # if it's ACCEPTED you can't do anything
            return states
        if num_status <= 1:  # if it's rejected or draft you can edit it
            states.append('UPDATE')
        if num_status >= 1:  # if it isn't REJECTED or ACCEPTED you can APPROVE it
            states.append('APPROVE')
        if num_status in [2, 3]:  # if it is in INTERNAL or DEPARTMENT REVIEW it can be rejected
            states.append('REJECT')
        return states

    def next_state(self):
        num_status = self.publish_status(numerical=True)
        if num_status == 0:
            # You can only get out of rejected state by saving
            message = "Page: {} is rejected.".format(self.guid)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status+1]
            self.status = new_status
            return "Updating page state for page: {} from {} to {}".format(self.guid, self.publish_status(), new_status)
        else:
            message = "Page: {} is already approved.".format(self.guid)
            raise AlreadyApproved(message)

    def reject(self):
        if self.status == 'ACCEPTED':
            message = "Page {} cannot be rejected a page in state: {}.".format(self.title, self.status)
            raise RejectionImpossible(message)

        rejected_state = publish_status.inv[0]
        message = "Updating page state for page: {} from {} to {}".format(self.title, self.status, rejected_state)
        self.status = rejected_state
        return message

    def not_editable(self):
        return self.publish_status(numerical=True) >= 2

    def eligible_for_build(self, beta_publication_states):
        if self.status in beta_publication_states and self.publication_date:
            return self.publication_date <= datetime.now().date()
        else:
            return self.status in beta_publication_states


class Meta:

    def __init__(self, guid, uri, parent, page_type, status=1, published=False):
        self.guid = guid
        self.uri = uri
        self.parent = parent
        self.type = page_type
        self.status = publish_status.inv[status]
        self.published = published

    def to_json(self):
        return json.dumps(
            {'uri': self.uri,
             'parent': self.parent,
             'type': self.type,
             'status': self.status,
             'guid': self.guid,
             'published': self.published
             })


class Dimension:

    def __init__(self, guid, title="", time_period="", summary="", chart="", table="", suppression_rules="",
                 disclosure_control="", type_of_statistic="", location="", source="", chart_source_data="",
                 table_source_data=""):
        self.guid = guid
        self.title = title
        self.time_period = time_period
        self.summary = summary
        self.suppression_rules = suppression_rules
        self.disclosure_control = disclosure_control
        self.type_of_statistic = type_of_statistic
        self.location = location
        self.source = source
        self.chart = chart
        self.table = table
        self.chart_source_data = chart_source_data
        self.table_source_data = table_source_data

    def __dict__(self):
        return {
            'guid': self.guid,
            'title': self.title,
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


class Page:
    def __init__(self, title, data, meta, dimensions=[], uploads=[]):
        self.meta = meta
        self.title = title
        self.guid = self.meta.guid  # this is really the page directory
        self.subtopics = []
        self.publication_date = None

        for key, value in data.items():
            if key == 'publication_date' and isinstance(value, str):
                value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(self, key, value)

        if dimensions:
            self.dimensions = [Dimension(guid=d['guid'],
                                         title=d['title'],
                                         time_period=d['time_period'],
                                         summary=d['summary'],
                                         suppression_rules=d['suppression_rules'],
                                         disclosure_control=d['disclosure_control'],
                                         type_of_statistic=d['type_of_statistic'],
                                         location=d['location'],
                                         source=d['source'],
                                         chart=d['chart'],
                                         table=d['table']) for d in dimensions]
        else:
            self.dimensions = []

        self.uploads = uploads

    def __hash__(self):
        return hash(self.guid)

    def __eq__(self, other):
        return self.guid == other.guid

    def __ne__(self, other):
        return not (self == other)

    def available_actions(self):
        """Returns the states available for this page -- WIP"""
        num_status = self.publish_status(numerical=True)
        states = []
        if num_status == 4:  # if it's ACCEPTED you can't do anything
            return states
        if num_status <= 1:  # if it's rejected or draft you can edit it
            states.append('UPDATE')
        if num_status >= 1:  # if it isn't REJECTED or ACCEPTED you can APPROVE it
            states.append('APPROVE')
        if num_status in [2, 3]:  # if it is in INTERNAL or DEPARTMENT REVIEW it can be rejected
            states.append('REJECT')
        return states

    def next_state(self):
        num_status = self.publish_status(numerical=True)
        if num_status == 0:
            # You can only get out of rejected state by saving
            message = "Page: {} is rejected.".format(self.guid)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status+1]
            self.meta.status = new_status
            return "Updating page state for page: {} from {} to {}".format(self.guid, self.publish_status(), new_status)
        else:
            message = "Page: {} is already approved.".format(self.guid)
            raise AlreadyApproved(message)

    def not_editable(self):
        return self.publish_status(numerical=True) >= 2

    def reject(self):
        if self.meta.status == 'ACCEPTED':
            message = "Page {} cannot be rejected a page in state: {}.".format(self.title, self.meta.status)
            raise RejectionImpossible(message)

        rejected_state = publish_status.inv[0]
        message = "Updating page state for page: {} from {} to {}".format(self.title, self.meta.status, rejected_state)
        self.meta.status = rejected_state
        return message

    def publish_status(self, numerical=False):
        current_status = self.meta.status.upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    def eligible_for_build(self, beta_publication_states):
        if self.meta.status in beta_publication_states and self.publication_date:
            return self.publication_date <= datetime.now().date()
        else:
            return self.meta.status in beta_publication_states

    def to_json(self):
        json_data = {
            "title": self.title,
            "measure_summary": self.measure_summary,
            "summary": self.summary,
            "geographic_coverage": self.geographic_coverage,
            "lowest_level_of_geography": self.lowest_level_of_geography,
            "time_covered": self.time_covered,
            "need_to_know": self.need_to_know,
            "ethnicity_definition_summary": self.ethnicity_definition_summary,
            "ethnicity_definition_detail": self.ethnicity_definition_detail,
            "source_text": self.source_text,
            "source_url": self.source_url,
            "department_source": self.department_source,
            "published_date": self.published_date,
            "last_update_date": self.last_update_date,
            "next_update_date": self.next_update_date,
            "frequency": self.frequency,
            "related_publications": self.related_publications,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "data_source_purpose": self.data_source_purpose,
            "methodology": self.methodology,
            "data_type": self.data_type,
            "suppression_rules": self.suppression_rules,
            "disclosure_control": self.disclosure_control,
            "estimation": self.estimation,
            "type_of_statistic": self.type_of_statistic,
            "qmi_url": self.qmi_url,
            "further_technical_information": self.further_technical_information,
            'subtopics': self.subtopics,
            'dimensions': [d.__dict__() for d in self.dimensions],
            'uploads': self.uploads
        }

        if self.publication_date:
            json_data["publication_date"] = self.publication_date.strftime('%Y-%m-%d')

        return json.dumps(json_data)

    def __str__(self):
        return self.guid

import json
from bidict import bidict

from application.cms.exceptions import CannotPublishRejected, AlreadyApproved, RejectionImpossible

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    ACCEPTED=4
)


class Meta:

    def __init__(self, guid, uri, parent, page_type, status=1):
        self.guid = guid
        self.uri = uri
        self.parent = parent
        self.type = page_type
        self.status = publish_status.inv[status]

    def to_json(self):
        return json.dumps(
            {'uri': self.uri,
             'parent': self.parent,
             'type': self.type,
             'status': self.status,
             'guid': self.guid,
             })


class Dimension:

    def __init__(self, guid, title="", time_period="", summary="", chart="", table=""):
        self.guid = guid
        self.title = title
        self.time_period = time_period
        self.summary = summary
        self.chart = chart
        self.table = table

    def __dict__(self):
        return {
            'guid': self.guid,
            'title': self.title,
            'time_period': self.time_period,
            'summary': self.summary,
            'chart': self.chart,
            'table': self.table
        }


class Page:
    def __init__(self, title, data, meta, dimensions=[], uploads=[]):
        self.meta = meta
        self.title = title
        self.guid = self.meta.guid  # this is really the page directory
        self.sections = []

        for key, value in data.items():
            setattr(self, key, value)

        if dimensions:
            self.dimensions = [Dimension(d['guid'],
                                         d['title'],
                                         d['time_period'],
                                         d['summary'],
                                         d['chart'],
                                         d['table']) for d in dimensions]
        else:
            self.dimensions = []

        self.uploads = uploads

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

    def to_json(self):
        json_data = {
            "title": self.title,
            'short_title': self.short_title,
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
            "population_or_sample": self.population_or_sample,
            "suppression_rules": self.suppression_rules,
            "disclosure_control": self.disclosure_control,
            "estimation": self.estimation,
            "qmi_url": self.qmi_url,
            "further_technical_information": self.further_technical_information,
            'sections': self.sections,
            'dimensions': [d.__dict__() for d in self.dimensions],
            'uploads': self.uploads
        }
        return json.dumps(json_data)

    def __str__(self):
        return self.guid

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

    def __init__(self, uri, parent, page_type, status=1):
        self.uri = uri
        self.parent = parent
        self.type = page_type
        self.status = publish_status.inv[status].lower()

    def to_json(self):
        return json.dumps(
            {'uri': self.uri,
             'parent': self.parent,
             'type': self.type,
             'status': self.status
             })


class Page:

    def __init__(self, title, description, meta, content=None):
        self.title = title
        self.guid = 'topic_%s' % title.lower().replace(' ', '')  # this is really the page directory
        self.description = description
        self.content = content
        self.sections = []
        self.meta = meta

    def available_actions(self):
        """Returns the states available for this page -- WIP"""
        # TODO: SINCE REJECT AND PUBLISH(APPROVE) are methods, EDIT should be a method as well
        # The above todo can come as part of the storage/page refactor
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
        return json.dumps(
            {'title': self.title,
             'description': self.description,
             'content': self.content,
             'sections': self.sections
             })

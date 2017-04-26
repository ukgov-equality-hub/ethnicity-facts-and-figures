
def format_page_guid(page_guid):
    _, name = page_guid.split('_')
    return '{}'.format(name).capitalize()


def format_approve_button(s):
    messages = {
        'INTERNAL_REVIEW': 'Submit for Internal Review',
        'DEPARTMENT_REVIEW': 'Approve for Department Review',
        'ACCEPTED': 'Approve for publishing'
    }
    return messages[s]


def format_status(status):
    return status.replace('_', ' ').title()

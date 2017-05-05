
def format_page_guid(page_guid):
    _, name = page_guid.split('_')
    return '{}'.format(name).capitalize()


def format_approve_button(s):
    messages = {
        'INTERNAL_REVIEW': 'Submit for Internal Review',
        'DEPARTMENT_REVIEW': 'Submit for Department Review',
        'ACCEPTED': 'Approve for publishing'
    }
    return messages[s]


def format_as_title(string):
    return string.replace('_', ' ').title()


def format_date_time(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")

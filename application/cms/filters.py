
def format_page_guid(page_guid):
    _, name = page_guid.split('_')
    return '{}'.format(name).capitalize()


def format_approve_button(s):
    messages = {
        'INTERNAL_REVIEW': 'Save &amp; Send to review',
        'DEPARTMENT_REVIEW': 'Send to department for review',
        'APPROVED': 'Approve for publishing'
    }
    return messages[s]


def format_as_title(string):
    if string == 'APPROVED':
        string = 'PUBLISHED'
    return string.replace('_', ' ').title()


def truncate_words(string):
    max_chars = 20
    truncated_string = ""
    if len(string) <= max_chars:
        return string
    else:
        words = string.split(' ')
        if len(words) == 1:
            return "{}...".format(string[:max_chars])
        else:
            for i, word in enumerate(words):
                if len(truncated_string + "{} ".format(word)) < max_chars:
                    if i == 0:
                        truncated_string += "{}".format(word)
                    else:
                        truncated_string += " {}".format(word)
                elif i != len(words):
                    truncated_string += "..."
                    break
            return truncated_string


def format_date_time(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def format_friendly_date(date):
    if date is None:
        return ''
    return date.strftime("%d %B %Y")


def format_versions(number):
    if number == 1:
        return '%s&nbsp;version' % number
    return '%s&nbsp;versions' % number


def format_status(state):
    status_names = {
      "DRAFT": "Draft",
      "INTERNAL_REVIEW": "Internal&nbsp;review",
      "DEPARTMENT_REVIEW": "Department&nbsp;review",
      "APPROVED": "Approved",
      "PUBLISHED": "Published",
      "REJECTED": "Rejected",
      "UNPUBLISHED": "Un&#8209;published"
    }
    return status_names[state] if state in status_names else state

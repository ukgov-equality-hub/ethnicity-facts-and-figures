def format_page_guid(page_guid):
    _, name = page_guid.split("_")
    return "{}".format(name).capitalize()


def format_approve_button(s):
    messages = {
        "INTERNAL_REVIEW": "Save &amp; Send to review",
        "DEPARTMENT_REVIEW": "Send to department for review",
        "APPROVED": "Approve for publishing",
    }
    return messages.get(s, "")


def format_date_time(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def format_friendly_date(date):
    if date is None:
        return ""
    return date.strftime("%d %B %Y")


def format_friendly_short_date_with_year(date):
    if date is None:
        return ""
    return date.strftime("%e %b %Y")


def format_friendly_short_date(date):
    if date is None:
        return ""
    return date.strftime("%d %b")


def format_versions(number):
    if number == 1:
        return "%s&nbsp;version" % number
    return "%s&nbsp;versions" % number


def format_status(state):
    status_names = {
        "DRAFT": "Draft",
        "INTERNAL_REVIEW": "Internal&nbsp;review",
        "DEPARTMENT_REVIEW": "Department&nbsp;review",
        "APPROVED": "Published",
        "REJECTED": "Rejected",
        "UNPUBLISHED": "Un&#8209;published",
    }
    return status_names.get(state, state.replace("_", "&nbsp;").capitalize())

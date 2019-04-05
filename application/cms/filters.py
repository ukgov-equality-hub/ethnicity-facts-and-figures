import bleach

from flask import Markup


def format_approve_button(s):
    messages = {
        "INTERNAL_REVIEW": "Save &amp; Send to review",
        "DEPARTMENT_REVIEW": "Send to department for review",
        "APPROVED": "Approve for publishing",
    }
    return messages.get(s, "")


def format_friendly_date(date):
    if date is None:
        return ""
    return date.strftime("%d %B %Y").lstrip("0")


def format_friendly_short_date_with_year(date):
    if date is None:
        return ""
    return date.strftime("%d %b %Y").lstrip("0")


def format_friendly_short_date(date):
    if date is None:
        return ""
    return date.strftime("%d %b").lstrip("0")


def index_of_last_initial_zero(list_):
    index_of_last_zero = None
    for index, value in enumerate(list_):
        if value == 0:
            index_of_last_zero = index
        else:
            break

    if index_of_last_zero is None:
        raise ValueError("List contains no 0 values")

    return index_of_last_zero


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


def yesno(state):
    if state is True:
        return "yes"
    elif state is False:
        return "no"

    return state


def models_to_dicts(items):
    """Call `.to_dict()` on each item of a list; useful for converting a list of model instances into a list of
    dictionaries suitable for e.g. converting to JSON."""
    return [item.to_dict() for item in items]


# This is used in the "Export" page to preserve line breaks in saved text area data to make any Markdown
# (e.g. bullet points) copy-and-pasteable from the exported version back into the form fields
def html_line_breaks(string):
    return Markup(bleach.clean(string).replace("\n", "<br />") if string else "")

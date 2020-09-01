from dataclasses import dataclass
from typing import List

from markupsafe import Markup


@dataclass
class ErrorSummaryMessage:
    text: str
    href: str


@dataclass
class TextFieldDiff:
    diff_markup: Markup
    updated_by: str


def copy_form_errors(from_form, to_form):
    for key, val in from_form.errors.items():
        to_form.errors[key] = val
        field = getattr(to_form, key)
        field.errors = val
        setattr(to_form, key, field)


def get_form_errors(forms=None, extra_non_form_errors=None):
    errors: List[ErrorSummaryMessage] = []

    if not forms:
        forms = []

    if not any(form.errors for form in forms) and not extra_non_form_errors:
        return errors

    for form in forms:
        for field_name, error_message in form.errors.items():
            form_field = getattr(form, field_name)
            errors.append(ErrorSummaryMessage(text=error_message[0], href=f"#{form_field.id}"))

    if extra_non_form_errors:
        errors.extend(extra_non_form_errors)

    return errors

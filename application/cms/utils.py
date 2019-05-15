from dataclasses import dataclass
from functools import partial
from typing import List

from flask import current_app
from markupsafe import Markup

from application.cms.forms import DataSourceForm


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
            errors.append(ErrorSummaryMessage(text=error_message[0], href=f"#{form_field.id}-label"))

    if extra_non_form_errors:
        errors.extend(extra_non_form_errors)

    return errors


def get_data_source_forms(request, measure_version, sending_to_review=False):
    include_csrf = current_app.config["WTF_CSRF_ENABLED"]

    if sending_to_review:
        include_csrf = False

    PartialDataSourceForm = partial(
        DataSourceForm, prefix="data-source-1-", sending_to_review=sending_to_review, meta={"csrf": include_csrf}
    )
    PartialDataSource2Form = partial(PartialDataSourceForm, prefix="data-source-2-")

    if measure_version:
        data_source_form = PartialDataSourceForm(obj=measure_version.primary_data_source)
        data_source_2_form = PartialDataSource2Form(obj=measure_version.secondary_data_source)

    else:
        data_source_form = PartialDataSourceForm()
        data_source_2_form = PartialDataSource2Form()

    return data_source_form, data_source_2_form

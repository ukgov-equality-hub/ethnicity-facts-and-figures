from functools import partial

from flask import flash, current_app

from application.cms.forms import DataSourceForm


def copy_form_errors(from_form, to_form):
    for key, val in from_form.errors.items():
        to_form.errors[key] = val
        field = getattr(to_form, key)
        field.errors = val
        setattr(to_form, key, field)


def flash_message_with_form_errors(lede="Please see below errors:", forms=None):
    if not forms:
        forms = []

    message = lede + "\n\n"

    for form_with_errors in forms:
        for field_name, error_message in form_with_errors.errors.items():
            form_field = getattr(form_with_errors, field_name)
            message += f"* [{form_field.label.text}](#{form_field.id}): {error_message[0]}\n"

    flash(message, "error")


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

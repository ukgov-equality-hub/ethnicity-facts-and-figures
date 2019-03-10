from functools import partial


from flask import current_app

from application.cms.forms import DataSourceForm


def copy_form_errors(from_form, to_form):
    for key, val in from_form.errors.items():
        to_form.errors[key] = val
        field = getattr(to_form, key)
        field.errors = val
        setattr(to_form, key, field)


def get_error_summary_data(title="Please see below errors:", forms=None):
    if not any(form.errors for form in forms):
        return {}

    if not forms:
        forms = []

    error_summary_data = {"title": title, "errors": []}
    for form in forms:
        for field_name, error_message in form.errors.items():
            form_field = getattr(form, field_name)
            error_summary_data["errors"].append(
                {"href": f"#{form_field.id}-label", "field": form_field.label.text, "text": error_message[0]}
            )

    return error_summary_data


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

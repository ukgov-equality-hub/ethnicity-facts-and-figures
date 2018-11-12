from functools import partial

from flask import flash, current_app

from application.cms.forms import DataSourceForm, DataSource2Form
from application.cms.models import TypeOfStatistic, FrequencyOfRelease


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


def get_data_source_forms(request, measure_page, sending_to_review=False):
    load_from_measure_page = request.method == "GET"
    include_csrf = current_app.config["WTF_CSRF_ENABLED"]

    if sending_to_review:
        include_csrf = False

    PartialDataSourceForm = partial(
        DataSourceForm,
        prefix="data-source-1-",
        type_of_statistic_model=TypeOfStatistic,
        frequency_of_release_model=FrequencyOfRelease,
        sending_to_review=sending_to_review,
        meta={"csrf": include_csrf},
    )
    PartialDataSource2Form = partial(PartialDataSourceForm, prefix="data-source-2-")

    if measure_page:
        if len(measure_page.data_sources) > 0:
            data_source_form = PartialDataSourceForm(obj=measure_page.data_sources[0])
        else:
            data_source_form = PartialDataSourceForm(
                **DataSourceForm.from_measure_page(measure_page) if load_from_measure_page else {}
            )

        if len(measure_page.data_sources) > 1:
            data_source_2_form = PartialDataSource2Form(obj=measure_page.data_sources[1])
        else:
            data_source_2_form = PartialDataSource2Form(
                **DataSource2Form.from_measure_page(measure_page) if load_from_measure_page else {}
            )
    else:
        data_source_form = PartialDataSourceForm()
        data_source_2_form = PartialDataSource2Form()

    return data_source_form, data_source_2_form

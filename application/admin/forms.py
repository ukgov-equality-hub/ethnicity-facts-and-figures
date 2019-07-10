from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Email

from typing import Sequence
from markupsafe import Markup
from flask import render_template

from application.form_fields import RDURadioField, RDUEmailField, ValidPublisherEmailAddress, RDUSearchField

from application.cms.models import DataSource


class AddUserForm(FlaskForm):
    email = RDUEmailField(
        label="Email address",
        validators=[
            Length(min=5, max=255),
            DataRequired(message="Enter an email address"),
            Email(message="Enter a valid email address"),
            ValidPublisherEmailAddress(),
        ],
    )
    user_type = RDURadioField(
        label="What type of user account?",
        choices=[("RDU_USER", "RDU CMS user"), ("DEPT_USER", "Departmental CMS user"), ("DEV_USER", "RDU Developer")],
        default="RDU_USER",
        validators=[DataRequired()],
    )


class DataSourceSearchForm(FlaskForm):

    q = RDUSearchField(label='<span class="govuk-visually-hidden">Search data sources</span>')


class DataSourceMergeForm(FlaskForm):

    keep = RDURadioField(label="Which one would you like to keep?")

    def _build_data_source_hint(self, data_source):
        return Markup(render_template("forms/labels/_merge_data_source_choice_hint.html", data_source=data_source))

    def __init__(self, data_sources: Sequence[DataSource], *args, **kwargs):
        super(DataSourceMergeForm, self).__init__(*args, **kwargs)

        self.keep.choices = [(data_source.id, data_source.title) for data_source in data_sources]

        hints = {data_source.id: self._build_data_source_hint(data_source) for data_source in data_sources}
        self.keep.choices_hints = hints

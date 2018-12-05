from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField, HiddenField, BooleanField
from wtforms.fields.html5 import DateField, EmailField, TelField
from wtforms.validators import DataRequired, Optional, ValidationError, Length

from application.cms.models import TypeOfData, UKCountry
from application.cms.form_fields import RDUCheckboxField, RDURadioField, RDUStringField, RDUURLField, RDUTextAreaField


class TypeOfDataRequiredValidator:
    def __call__(self, form, field):
        administrative = form.data.get("administrative_data", False)
        survey = form.data.get("survey_data", False)

        if not any([administrative, survey]):
            raise ValidationError("Select at least one")


class AreaCoveredRequiredForReviewValidator:
    def __call__(self, form, field):
        if getattr(form, "sending_to_review", False):
            england = form.data.get("england", False)
            wales = form.data.get("wales", False)
            scotland = form.data.get("scotland", False)
            northern_ireland = form.data.get("northern_ireland", False)

            if not any([england, wales, scotland, northern_ireland]):
                raise ValidationError("Select at least one")


class FrequencyOfReleaseOtherRequiredValidator:
    def __call__(self, form, field):
        message = "Other selected but no value has been entered"

        if (
            form.frequency_of_release_id.data
            and form.frequency_of_release_id.choices[form.frequency_of_release_id.data - 1][1].lower() == "other"
        ):
            if not form.frequency_of_release_other.data:
                raise ValidationError(message)


class RequiredForReviewValidator(DataRequired):
    """
    This validator is designed for measure pages which can have their progress saved half-way through filling in
    fields, but need to ensure certain fields have been filled in when the measure page is being submitted for review.

    This validator checks whether the form has been called with the `sending_to_review` argument. If it has, then
    it applies the DataRequired validator to all fields with this validator. If it has not, then you can specify whether
    or not the field should be considered optional - this is useful for e.g. radio fields, which by default need a
    value selected.

    Note: if you use the `else_optional` functionality of this validator, the validator should be the last entry in the
    validation chain, as `Optional` validators end the validation chain.
    """

    field_flags = tuple()

    def __init__(self, message=None, else_optional=False):
        self.message = message
        self.else_optional = else_optional
        super().__init__(message=message)

    def __call__(self, form, field):
        if getattr(form, "sending_to_review", False):
            super().__call__(form, field)

        elif self.else_optional:
            Optional().__call__(form, field)


class DataSourceForm(FlaskForm):
    # Updated via JS if a user wants to remove the data source
    remove_data_source = RDUCheckboxField(
        label="Remove data source", choices=[("remove-source", "Remove source")], coerce=lambda x: x if x else ""
    )

    title = RDUStringField(
        label="Title of data source",
        hint="For example, Crime and Policing Survey",
        validators=[RequiredForReviewValidator(), Length(max=255)],
    )

    type_of_data = RDUCheckboxField(label="Type of data", enum=TypeOfData, validators=[RequiredForReviewValidator()])
    type_of_statistic_id = RDURadioField(
        label="Type of statistic", coerce=int, validators=[RequiredForReviewValidator("Select one", else_optional=True)]
    )

    publisher_id = RDUStringField(
        label="Source data published by", hint="For example, Ministry of Justice", validators=[RequiredForReviewValidator()]
    )
    source_url = RDUURLField(
        label="Link to data source",
        hint=(
            "Link to a web page where the data was originally published."
            " Don’t link directly to a spreadsheet or a PDF. <a href=\"https://www.gov.uk/government/statistics/youth-justice-annual-statistics-2016-to-2017\" target=\"_blank\">View example</a> (this will open a new page)."
        ),
        validators=[RequiredForReviewValidator(), Length(max=255)],
    )

    publication_date = RDUStringField(label="Source data publication date", hint="Use the format dd/mm/yyyy. For example, 26/03/2018. If you’re using a revised version of the data, give that publication date.")
    note_on_corrections_or_updates = RDUTextAreaField(label="Corrections or updates (optional)", hint="For example, explain if you’ve used a revised version of the data")

    frequency_of_release_other = RDUStringField(label="Other publication frequency", validators=[Length(max=255)])
    frequency_of_release_id = RDURadioField(
        label="How often is the source data published?",
        coerce=int,
        validators=[
            FrequencyOfReleaseOtherRequiredValidator(),
            RequiredForReviewValidator("Select one", else_optional=True),
        ],
    )

    purpose = RDUTextAreaField(label="Purpose of data source", hint="Explain why this data’s been collected and how it will be used", validators=[RequiredForReviewValidator()])

    def __init__(self, sending_to_review=False, *args, **kwargs):
        super(DataSourceForm, self).__init__(*args, **kwargs)

        self.sending_to_review = sending_to_review

        type_of_statistic_choices = []
        type_of_statistic_model = kwargs.get("type_of_statistic_model", None)
        if type_of_statistic_model:
            type_of_statistic_choices = type_of_statistic_model.query.order_by("position").all()
        self.type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in type_of_statistic_choices]

        frequency_of_release_choices = []
        frequency_of_release_model = kwargs.get("frequency_of_release_model", None)
        if frequency_of_release_model:
            frequency_of_release_choices = frequency_of_release_model.query.order_by("position").all()
        self.frequency_of_release_id.choices = [
            (choice.id, choice.description) for choice in frequency_of_release_choices
        ]
        self.frequency_of_release_id.set_other_field(self.frequency_of_release_other)


class MeasurePageForm(FlaskForm):
    db_version_id = HiddenField()
    title = StringField(label="Title", validators=[DataRequired(), Length(max=255)])
    internal_reference = StringField(label="Measure code (optional)")
    publication_date = DateField(label="Publication date", format="%Y-%m-%d", validators=[Optional()])
    time_covered = StringField(label="Time period covered", validators=[RequiredForReviewValidator()])

    england = BooleanField(label=UKCountry.ENGLAND.value, validators=[AreaCoveredRequiredForReviewValidator()])
    wales = BooleanField(label=UKCountry.WALES.value)
    scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)

    lowest_level_of_geography_id = RDURadioField(
        label="Geographic breakdown", validators=[RequiredForReviewValidator("Select one", else_optional=True)]
    )
    suppression_and_disclosure = TextAreaField(label="Suppression rules and disclosure control (optional)")
    estimation = TextAreaField(label="Rounding (optional)")

    # Commentary
    summary = TextAreaField(label="Main points", validators=[RequiredForReviewValidator()])
    measure_summary = TextAreaField(label="What the data measures", validators=[RequiredForReviewValidator()])
    need_to_know = TextAreaField(label="Things you need to know", validators=[RequiredForReviewValidator()])
    ethnicity_definition_summary = TextAreaField(label="The ethnic categories used in this data", validators=[RequiredForReviewValidator()])

    methodology = TextAreaField(label="Methodology", validators=[RequiredForReviewValidator()])
    related_publications = TextAreaField(label="Related publications (optional)")
    qmi_url = StringField(label="Quality Methodology Information URL")
    further_technical_information = TextAreaField(label="Further technical information (optional)")

    # Edit summaries
    external_edit_summary = TextAreaField(label="Changes to previous version", validators=[RequiredForReviewValidator()])
    internal_edit_summary = TextAreaField(label="Notes (for internal use only)")

    def __init__(self, sending_to_review=False, *args, **kwargs):
        super(MeasurePageForm, self).__init__(*args, **kwargs)

        self.sending_to_review = sending_to_review

        choice_model = kwargs.get("lowest_level_of_geography_choices", None)
        choices = []
        if choice_model:
            geographic_choices = choice_model.query.order_by("position").all()
            for choice in geographic_choices:
                if choice.description is not None:
                    description = "%s %s" % (choice.name, choice.description)
                    choices.append((choice.name, description))
                else:
                    choices.append((choice.name, choice.name))

        self.lowest_level_of_geography_id.choices = choices

    def error_items(self):
        return self.errors.items()


class DimensionForm(FlaskForm):
    title = StringField(label="Title", validators=[DataRequired()])
    time_period = StringField(label="Time period covered")
    summary = TextAreaField(label="Summary")

    def __init__(self, *args, **kwargs):
        super(FlaskForm, self).__init__(*args, **kwargs)


class UploadForm(FlaskForm):
    guid = StringField()
    upload = FileField(
        label="File in CSV format", validators=[DataRequired(message="Please choose a file for users to download")]
    )
    title = StringField(label="Title", validators=[DataRequired()])
    description = TextAreaField()


class DimensionRequiredForm(DimensionForm):
    title = StringField(label="Title", validators=[DataRequired()])
    summary = TextAreaField(label="Summary", validators=[DataRequired()])


class NewVersionForm(FlaskForm):
    version_type = RadioField(
        label="New version type", validators=[DataRequired()], choices=[("minor", "Minor"), ("major", "Major")]
    )

from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import StringField, TextAreaField, FileField, HiddenField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Optional, ValidationError, Length, StopValidation, InputRequired

from application.cms.form_fields import RDUCheckboxField, RDURadioField, RDUStringField, RDUURLField, RDUTextAreaField
from application.cms.models import (
    TypeOfData,
    UKCountry,
    MeasureVersion,
    NewVersionType,
    LowestLevelOfGeography,
    FrequencyOfRelease,
    TypeOfStatistic,
)
from application.utils import get_bool


class TypeOfDataRequiredValidator:
    def __call__(self, form, field):
        administrative = form.data.get("administrative_data", False)
        survey = form.data.get("survey_data", False)

        if not any([administrative, survey]):
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


class RequiredForReviewValidator(InputRequired):
    """
    This validator is designed for measure pages which can have their progress saved half-way through filling in
    fields, but need to ensure certain fields have been filled in when the measure page is being submitted for review.

    This validator checks whether the form has been called with the `sending_to_review` argument. If it has, then
    it applies the InputRequired validator to all fields with this validator. If it has not, then you can specify
    whether or not the field should be considered optional - this is useful for e.g. radio fields, which by default need
    a value selected.

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
        label="Source data published by",
        hint="For example, Ministry of Justice",
        validators=[RequiredForReviewValidator()],
    )
    source_url = RDUURLField(
        label="Link to data source",
        hint=Markup(
            "Link to a web page where the data was originally published. "
            "Don’t link directly to a spreadsheet or a PDF. "
            '<a href="https://www.gov.uk/government/statistics/youth-justice-annual-statistics-2016-to-2017" '
            'target="_blank">View example</a> (this will open a new page).'
        ),
        validators=[RequiredForReviewValidator(), Length(max=255)],
    )

    publication_date = RDUStringField(
        label="Source data publication date",
        hint="For example, 26/03/2018. If you’re using a revised version of the data, give that publication date.",
    )
    note_on_corrections_or_updates = RDUTextAreaField(
        label="Corrections or updates (optional)",
        hint="For example, explain if you’ve used a revised version of the data",
    )

    frequency_of_release_other = RDUStringField(label="Other publication frequency", validators=[Length(max=255)])
    frequency_of_release_id = RDURadioField(
        label="How often is the source data published?",
        coerce=int,
        validators=[
            FrequencyOfReleaseOtherRequiredValidator(),
            RequiredForReviewValidator("Select one", else_optional=True),
        ],
    )

    purpose = RDUTextAreaField(
        label="Purpose of data source",
        hint="Explain why this data’s been collected and how it will be used",
        validators=[RequiredForReviewValidator()],
    )

    def __init__(self, sending_to_review=False, *args, **kwargs):
        super(DataSourceForm, self).__init__(*args, **kwargs)

        self.sending_to_review = sending_to_review

        self.type_of_statistic_id.choices = [
            (choice.id, choice.internal) for choice in TypeOfStatistic.query.order_by("position").all()
        ]

        self.frequency_of_release_id.choices = [
            (choice.id, choice.description) for choice in FrequencyOfRelease.query.order_by("position").all()
        ]
        self.frequency_of_release_id.set_other_field(self.frequency_of_release_other)


class MeasureVersionForm(FlaskForm):
    class NotRequiredForMajorVersions:
        def __call__(self, form: "MeasureVersionForm", field):
            if not form.is_minor_update:
                field.errors[:] = []
                raise StopValidation()

    db_version_id = HiddenField()
    title = RDUStringField(
        label="Title",
        validators=[DataRequired(), Length(max=255)],
        hint="For example, ‘Self-harm by young people in custody’",
        strip_whitespace=True,
    )
    internal_reference = RDUStringField(
        label="Measure code (optional)",
        hint="This is for internal use by the Race Disparity Unit",
        strip_whitespace=True,
    )
    published_at = DateField(label="Publication date", format="%Y-%m-%d", validators=[Optional()])
    time_covered = RDUStringField(
        label="Time period covered",
        validators=[RequiredForReviewValidator()],
        hint="For example, ‘2016 to 2017’, or ‘2014/15 to 2016/17’",
        strip_whitespace=True,
    )

    area_covered = RDUCheckboxField(label="Areas covered", enum=UKCountry, validators=[RequiredForReviewValidator()])

    lowest_level_of_geography_id = RDURadioField(
        label="Geographic breakdown",
        hint="Select the most detailed type of geographic breakdown available in the data",
        validators=[RequiredForReviewValidator("Select one", else_optional=True)],
    )
    suppression_and_disclosure = RDUTextAreaField(
        label="Suppression rules and disclosure control (optional)",
        hint="If any data has been excluded from the analysis, explain why",
        extended_hint="_suppression_and_disclosure.html",
        strip_whitespace=True,
    )
    estimation = RDUTextAreaField(
        label="Rounding (optional)",
        hint="For example, ‘Percentages are rounded to one decimal place’",
        strip_whitespace=True,
    )

    summary = RDUTextAreaField(
        label="Main points",
        validators=[RequiredForReviewValidator()],
        hint="Summarise the main findings and highlight any serious caveats in the quality of the data",
        extended_hint="_summary.html",
        strip_whitespace=True,
    )

    measure_summary = RDUTextAreaField(
        label="What the data measures",
        validators=[RequiredForReviewValidator()],
        hint=(
            "Explain what the data is analysing, what’s included in categories labelled as ‘Other’ and define any "
            "terms users might not understand"
        ),
        strip_whitespace=True,
    )

    need_to_know = RDUTextAreaField(
        label="Things you need to know",
        validators=[RequiredForReviewValidator()],
        hint="Outline how the data was collected and explain any limitations",
        extended_hint="_things_you_need_to_know.html",
        strip_whitespace=True,
    )

    ethnicity_definition_summary = RDUTextAreaField(
        label="The ethnic categories used in this data",
        validators=[RequiredForReviewValidator()],
        hint=Markup(
            "Say which ethnic groups are included in the data and why. "
            "For the most common ethnic categorisations, see the "
            '<a href="https://guide.ethnicity-facts-figures.service.gov.uk/a-z#ethnic-categories" target="_blank">'
            "Style guide A to Z</a> (this will open a new page)."
        ),
        strip_whitespace=True,
    )

    methodology = RDUTextAreaField(
        label="Methodology",
        validators=[RequiredForReviewValidator()],
        hint="Explain your methods in clear, simple language",
        extended_hint="_methodology.html",
        strip_whitespace=True,
    )
    related_publications = RDUTextAreaField(
        label="Related publications (optional)", extended_hint="_related_publications.html", strip_whitespace=True
    )
    qmi_url = RDUURLField(label="Link to quality and methodology information", strip_whitespace=True)
    further_technical_information = RDUTextAreaField(
        label="Further technical information (optional)", strip_whitespace=True
    )

    # Edit summaries
    update_corrects_data_mistake = RDURadioField(
        label="Does this update correct a mistake in the data?",
        choices=((True, "Yes"), (False, "No")),
        coerce=lambda value: None if value is None else get_bool(value),
        validators=[
            NotRequiredForMajorVersions(),
            RequiredForReviewValidator("This field is required", else_optional=True),
        ],
    )
    external_edit_summary = RDUTextAreaField(
        label="Changes to previous version",
        validators=[RequiredForReviewValidator()],
        hint=(
            "If you’ve updated only a sentence or two, add the updated content here. Otherwise, briefly summarise "
            "what’s changed in the latest version (for example, ‘Updated with new data’ or ‘Minor changes for style "
            "and accuracy’)."
        ),
        strip_whitespace=True,
    )
    internal_edit_summary = RDUTextAreaField(
        label="Notes (for internal use - optional)",
        hint="Include any additional information someone might need if they’re working on this page in the future",
        strip_whitespace=True,
    )

    def __init__(self, is_minor_update: bool, sending_to_review=False, *args, **kwargs):
        super(MeasureVersionForm, self).__init__(*args, **kwargs)

        self.is_minor_update = is_minor_update
        self.sending_to_review = sending_to_review

        # Major versions are not considered "corrections to data mistakes", and the question is not shown to end users.
        # So let's provide the default value here.
        if not self.is_minor_update:
            self.update_corrects_data_mistake.data = False

        choices = []
        geographic_choices = LowestLevelOfGeography.query.order_by("position").all()
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
    title = RDUStringField(
        label="Title", hint="For example, ‘Employment by ethnicity and gender’", validators=[DataRequired()]
    )
    time_period = RDUStringField(label="Time period covered", hint="For example, ‘2015/16’")
    summary = RDUTextAreaField(label="Summary", extended_hint="_dimension_summary.html")

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
    version_type = RDURadioField(label=Markup("<b>New version type:</b>"), validators=[DataRequired()])

    def __init__(self, measure_version: MeasureVersion, *args, **kwargs):
        super(NewVersionForm, self).__init__(*args, **kwargs)

        next_minor_version = measure_version.next_minor_version()
        next_major_version = measure_version.next_major_version()

        self.version_type.choices = [
            (
                NewVersionType.MINOR_UPDATE.value,
                Markup(f"<b>{next_minor_version}</b>Edit this edition (eg for clarifications or corrections)"),
            ),
            (
                NewVersionType.MAJOR_UPDATE.value,
                Markup(f"<b>{next_major_version}</b>Create new edition (eg after new data becomes available)"),
            ),
        ]

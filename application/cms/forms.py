from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField, HiddenField, BooleanField
from wtforms.fields.html5 import DateField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional, ValidationError

from application.cms.models import TypeOfData, UKCountry
from application.cms.form_fields import RDUCheckboxField, RDURadioField, RDUStringField, RDUURLField, RDUTextAreaField


class TypeOfDataRequiredValidator:
    def __call__(self, form, field):
        administrative = form.data.get("administrative_data", False)
        survey = form.data.get("survey_data", False)

        if not any([administrative, survey]):
            raise ValidationError("Select at least one")


class AreaCoveredRequiredValidator:
    def __call__(self, form, field):
        england = form.data.get("england", False)
        wales = form.data.get("wales", False)
        scotland = form.data.get("scotland", False)
        northern_ireland = form.data.get("northern_ireland", False)

        if not any([england, wales, scotland, northern_ireland]):
            raise ValidationError("Select at least one")


class FrequencyOtherRequiredValidator:
    """DEPRECATED: Compatibility validator for old measure pages, before data source was separated"""

    def __call__(self, form, field):
        message = "Other selected but no value has been entered"
        if form.frequency_id.data and form.frequency_id.choices[form.frequency_id.data - 1][1].lower() == "other":
            if not form.frequency_other.data:
                form.errors["frequency_other"] = ["This field is required"]
                raise ValidationError(message)

        if form.secondary_source_1_frequency_id.data is not None:
            if (
                form.secondary_source_1_frequency_id.data
                and form.secondary_source_1_frequency_id.choices[form.secondary_source_1_frequency_id.data - 1][
                    1
                ].lower()
                == "other"
            ):
                if not form.secondary_source_1_frequency_other.data:
                    form.errors["secondary_source_1_frequency_other"] = ["This field is required"]
                    raise ValidationError(message)


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
    remove_data_source = HiddenField()  # Updated via JS if a user wants to remove the data source

    title = RDUStringField(
        label="Title of data source",
        hint="For example, Crime and Policing Survey",
        validators=[RequiredForReviewValidator()],
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
        validators=[RequiredForReviewValidator()],
    )
    publication_date = RDUStringField(label="Source data publication date", hint="Use the format dd/mm/yyyy. For example, 26/03/2018. If you’re using a revised version of the data, give that publication date.")
    note_on_corrections_or_updates = RDUTextAreaField(label="Corrections or updates (optional)", hint="For example, explain if you’ve used a revised version of the data")

    frequency_of_release_other = RDUStringField(label="Other publication frequency")
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

    # BEGIN COMPATABILITY BLOCK

    MEASURE_PAGE_DATA_SOURCE_MAP = {
        "title": "source_text",
        "type_of_data": "type_of_data",
        "type_of_statistic_id": "type_of_statistic_id",
        "publisher_id": "department_source_id",
        "source_url": "source_url",
        "publication_date": "published_date",
        "note_on_corrections_or_updates": "note_on_corrections_or_updates",
        "frequency_of_release_id": "frequency_id",
        "frequency_of_release_other": "frequency_other",
        "purpose": "data_source_purpose",
    }
    MEASURE_PAGE_DATA_SOURCE_PREFIX = "data-source-1-"

    @classmethod
    def from_measure_page(cls, measure_page):
        data = {}
        for data_source_attr, measure_page_attr in cls.MEASURE_PAGE_DATA_SOURCE_MAP.items():
            data_source_attr = data_source_attr
            attr_value = getattr(measure_page, measure_page_attr)
            if attr_value:
                data[data_source_attr] = attr_value
            else:
                data[data_source_attr] = ""
        return data

    # END COMPATABILITY BLOCK


class DataSource2Form(DataSourceForm):
    title = RDUStringField(label="Title of data source", hint="For example, Annual Population Survey")

    # BEGIN COMPATABILITY BLOCK

    MEASURE_PAGE_DATA_SOURCE_MAP = {
        "title": "secondary_source_1_title",
        "type_of_data": "secondary_source_1_type_of_data",
        "type_of_statistic_id": "secondary_source_1_type_of_statistic_id",
        "publisher_id": "secondary_source_1_publisher_id",
        "source_url": "secondary_source_1_url",
        "publication_date": "secondary_source_1_date",
        "note_on_corrections_or_updates": "secondary_source_1_note_on_corrections_or_updates",
        "frequency_of_release_id": "secondary_source_1_frequency_id",
        "frequency_of_release_other": "secondary_source_1_frequency_other",
        "purpose": "secondary_source_1_data_source_purpose",
    }
    MEASURE_PAGE_DATA_SOURCE_PREFIX = "data-source-2-"

    # END COMPATABILITY BLOCK


class MeasurePageForm(FlaskForm):
    db_version_id = HiddenField()
    title = StringField(label="Title", validators=[DataRequired()])
    internal_reference = StringField(label="Measure code (optional)")
    publication_date = DateField(label="Publication date", format="%Y-%m-%d", validators=[Optional()])
    time_covered = StringField(label="Time period covered")

    england = BooleanField(label=UKCountry.ENGLAND.value)
    wales = BooleanField(label=UKCountry.WALES.value)
    scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)

    lowest_level_of_geography_id = RDURadioField(label="Geographic breakdown", validators=[Optional()])
    suppression_and_disclosure = TextAreaField(label="Suppression rules and disclosure control (optional)")
    estimation = TextAreaField(label="Rounding (optional)")

    # Commentary
    summary = TextAreaField(label="Main points")
    measure_summary = TextAreaField(label="What the data measures")
    need_to_know = TextAreaField(label="Things you need to know")
    ethnicity_definition_summary = TextAreaField(label="The ethnic categories used in this data")

    methodology = TextAreaField(label="Methodology")
    related_publications = TextAreaField(label="Related publications (optional)")
    qmi_url = StringField(label="Quality Methodology Information URL")
    further_technical_information = TextAreaField(label="Further technical information (optional)")

    # Edit summaries
    external_edit_summary = TextAreaField(label="Changes to previous version")
    internal_edit_summary = TextAreaField(label="Notes (for internal use only)")

    # Contact details
    contact_name = StringField(label="Name")
    contact_email = EmailField(label="Email")
    contact_phone = TelField(label="Phone number")

    contact_2_name = StringField(label="Name")
    contact_2_email = EmailField(label="Email")
    contact_2_phone = TelField(label="Phone number")

    def __init__(self, *args, **kwargs):
        super(MeasurePageForm, self).__init__(*args, **kwargs)

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


class MeasurePageRequiredForm(MeasurePageForm):
    def __init__(self, *args, **kwargs):
        kwargs["meta"] = kwargs.get("meta") or {}
        super(MeasurePageRequiredForm, self).__init__(*args, **kwargs)

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

    time_covered = StringField(label="Time period covered", validators=[DataRequired()])

    england = BooleanField(label=UKCountry.ENGLAND.value, validators=[AreaCoveredRequiredValidator()])
    wales = BooleanField(label=UKCountry.WALES.value)
    scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)

    lowest_level_of_geography_id = RadioField(
        label="Lowest level of geography", validators=[DataRequired(message="Select one")]
    )

    measure_summary = TextAreaField(label="What the data measures", validators=[DataRequired()])
    summary = TextAreaField(label="Main points", validators=[DataRequired()])
    need_to_know = TextAreaField(label="Things you need to know", validators=[DataRequired()])
    ethnicity_definition_summary = TextAreaField(
        label="The ethnic categories used in this data", validators=[DataRequired()]
    )

    methodology = TextAreaField(label="Methodology", validators=[DataRequired()])
    internal_edit_summary = StringField(label="Internal edit summary", validators=[DataRequired()])

    def error_items(self):
        items = self.errors.items()
        filtered = [item for item in items if item[0] != "survey_data"]
        return filtered


class DimensionRequiredForm(DimensionForm):
    def __init__(self, *args, **kwargs):
        kwargs["meta"] = kwargs.get("meta") or {}

        super(DimensionRequiredForm, self).__init__(*args, **kwargs)

    title = StringField(label="Title", validators=[DataRequired()])
    summary = TextAreaField(label="Summary", validators=[DataRequired()])


class NewVersionForm(FlaskForm):
    version_type = RadioField(
        label="New version type", validators=[DataRequired()], choices=[("minor", "Minor"), ("major", "Major")]
    )

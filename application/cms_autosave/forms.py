from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, RadioField, HiddenField, SelectMultipleField, widgets
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, Optional

from application.cms.forms import FrequencyOtherRequiredValidator
from application.cms.models import UKCountry, TypeOfData


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

    def pre_validate(self, form):
        """pre_validation is disabled as some values (eg checkbox lists) need to be processed first"""


class MeasurePageAutosaveForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(MeasurePageAutosaveForm, self).__init__(*args, **kwargs)
        choice_model = kwargs.get("frequency_choices", None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by("position").all()
        self.frequency_id.choices = [(choice.id, choice.description) for choice in choices]
        self.secondary_source_1_frequency_id.choices = [(choice.id, choice.description) for choice in choices]

        choice_model = kwargs.get("type_of_statistic_choices", None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by("position").all()
        self.type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in choices]
        self.secondary_source_1_type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in choices]

        # UK is a 'special' value that gets set if all four countries of the UK are selected - no UK checkbox shown
        self.area_covered.choices = [(choice, choice.value) for choice in UKCountry if choice.value != "UK"]
        if self.area_covered.data == ["UKCountry.UK"]:
            self.area_covered.data = [
                "UKCountry.ENGLAND",
                "UKCountry.NORTHERN_IRELAND",
                "UKCountry.SCOTLAND",
                "UKCountry.WALES",
            ]

        self.type_of_data.choices = self.secondary_source_1_type_of_data.choices = [
            (choice, choice.value) for choice in TypeOfData
        ]

    # Metadata
    db_version_id = HiddenField()
    title = StringField(label="measure_title", validators=[DataRequired()])
    area_covered = MultiCheckboxField(label="Area covered")
    time_covered = StringField(label="Time period")

    # Commentary
    summary = TextAreaField(label="Main points")
    need_to_know = TextAreaField(label="Things you need to know")
    measure_summary = TextAreaField(label="What the data measures")
    ethnicity_definition_summary = TextAreaField(label="The ethnic categories used in this data")

    # Methodology
    methodology = TextAreaField(label="Methodology")
    suppression_and_disclosure = TextAreaField(label="Suppression rules and disclosure control")
    estimation = TextAreaField(label="Rounding")
    related_publications = TextAreaField(label="Related publications")
    qmi_url = StringField(label="Quality and methodology information")
    further_technical_information = TextAreaField(label="Further technical information")

    # Primary data source
    source_text = StringField(label="Title of data source")
    source_url = URLField(label="URL")
    type_of_data = MultiCheckboxField(label="Type of data")
    type_of_statistic_id = RadioField(label="Type of statistic", coerce=int, validators=[Optional()])
    department_source = StringField(label="Publisher")
    published_date = StringField(label="Publication release date")
    note_on_corrections_or_updates = TextAreaField(label="Note on corrections or updates")
    frequency_id = RadioField(
        label="Publication frequency", coerce=int, validators=[Optional(), FrequencyOtherRequiredValidator()]
    )
    frequency_other = StringField(label="Other")
    data_source_purpose = TextAreaField(label="Purpose of data source")

    # Secondary data source
    secondary_source_1_title = StringField(label="Title of data source")
    secondary_source_1_url = URLField(label="URL")
    secondary_source_1_type_of_data = MultiCheckboxField(label="Type of data")
    secondary_source_1_type_of_statistic_id = RadioField(label="Type of statistic", coerce=int, validators=[Optional()])
    secondary_source_1_publisher = StringField(label="Publisher")
    secondary_source_1_date = StringField(label="Publication release date")
    secondary_source_1_note_on_corrections_or_updates = TextAreaField(label="Note on corrections or updates")
    secondary_source_1_frequency_id = RadioField(
        label="Publication frequency", coerce=int, validators=[Optional(), FrequencyOtherRequiredValidator()]
    )
    secondary_source_1_frequency_other = StringField(label="Other")
    secondary_source_1_data_source_purpose = TextAreaField(label="Purpose of data source")

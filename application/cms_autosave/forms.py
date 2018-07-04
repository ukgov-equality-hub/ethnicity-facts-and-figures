from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField, HiddenField, BooleanField, SelectMultipleField, \
    widgets
from wtforms.fields.html5 import DateField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional, ValidationError

from application.cms.forms import FrequencyOtherRequiredValidator


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class MeasurePageAutosaveForm(FlaskForm):

    def __init__(self, *args, **kwargs):
        super(MeasurePageAutosaveForm, self).__init__(*args, **kwargs)
        choice_model = kwargs.get('frequency_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()
        self.frequency_id.choices = [(choice.id, choice.description) for choice in choices]
        self.secondary_source_1_frequency_id.choices = [(choice.id, choice.description) for choice in choices]

        choice_model = kwargs.get('type_of_statistic_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()
        self.type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in choices]
        self.secondary_source_1_type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in choices]

    # Metadata
    db_version_id = HiddenField()
    title = StringField(label='measure_title', validators=[DataRequired()])
    area_covered = MultiCheckboxField(label='Area covered', choices=['England', 'Ireland', 'Scotland', 'Wales'])
    time_covered = StringField(label='Time period')

    # Commentary
    summary = TextAreaField(label='Main points')
    need_to_know = TextAreaField(label='Things you need to know')
    measure_summary = TextAreaField(label='What the data measures')
    ethnicity_definition_summary = TextAreaField(label='The ethnic categories used in this data')

    # title = StringField(label='Title', validators=[DataRequired()])
    # internal_reference = StringField(label='Internal reference (optional)')
    # publication_date = DateField(label='Publication date', format='%Y-%m-%d', validators=[Optional()])
    # time_covered = StringField(label='Time period covered')
    #
    # england = BooleanField(label=UKCountry.ENGLAND.value)
    # wales = BooleanField(label=UKCountry.WALES.value)
    # scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    # northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)
    #
    # lowest_level_of_geography_id = RadioField(label='Lowest level of geography', validators=[Optional()])
    #
    # # Primary source
    # source_text = StringField(label='Title of data source')
    #
    # # Type of data
    # administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value)
    # survey_data = BooleanField(label=TypeOfData.SURVEY.value)
    #
    type_of_statistic_id = RadioField(label='Type of statistic', coerce=int, validators=[Optional()])
    #
    department_source = StringField(label='Publisher')

    # source_url = URLField(label='URL')
    # published_date = StringField(label='Publication release date')
    # note_on_corrections_or_updates = TextAreaField(label='Note on corrections or updates')
    frequency_id = RadioField(label='Publication frequency',
                              coerce=int,
                              validators=[Optional(), FrequencyOtherRequiredValidator()])
    frequency_other = StringField(label='Other')

    #
    # data_source_purpose = TextAreaField(label='Purpose of data source')
    # suppression_and_disclosure = TextAreaField(label='Suppression rules and disclosure control')
    # estimation = TextAreaField(label='Rounding')
    #
    # # End primary source
    #
    # # Secondary source
    # secondary_source_1_title = StringField(label='Title of data source')
    #
    # # Secondary source type of data
    # secondary_source_1_administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value)
    # secondary_source_1_survey_data = BooleanField(label=TypeOfData.SURVEY.value)
    #
    secondary_source_1_type_of_statistic_id = RadioField(label='Type of statistic', coerce=int,
                                                         validators=[Optional()])
    #
    secondary_source_1_publisher = StringField(label='Publisher')
    #
    # secondary_source_1_url = URLField(label='URL')
    # secondary_source_1_date = StringField(label='Publication release date')
    # secondary_source_1_note_on_corrections_or_updates = TextAreaField(label='Note on corrections or updates')
    secondary_source_1_frequency_id = RadioField(label='Publication frequency',
                                                 coerce=int,
                                                 validators=[Optional(), FrequencyOtherRequiredValidator()])
    secondary_source_1_frequency_other = StringField(label='Other')
    #
    # secondary_source_1_data_source_purpose = TextAreaField(label='Purpose of data source')
    # secondary_source_1_suppression_and_disclosure = TextAreaField(label='Suppression rules and disclosure control')
    # secondary_source_1_estimation = TextAreaField(label='Rounding')
    #
    # # End secondary source
    #
    # # Commentary
    # summary = TextAreaField(label='Main points')
    # measure_summary = TextAreaField(label='What the data measures')
    # need_to_know = TextAreaField(label='Things you need to know')
    # ethnicity_definition_summary = TextAreaField(label='The ethnic categories used in this data')
    #
    # methodology = TextAreaField(label='Methodology')
    # related_publications = TextAreaField(label='Related publications')
    # qmi_url = StringField(label='Quality Methodology Information URL')
    # further_technical_information = TextAreaField(label='Further technical information')
    #
    # # Edit summaries
    # external_edit_summary = TextAreaField(label='External edit summary')
    # internal_edit_summary = TextAreaField(label='Internal edit summary')
    #
    # # Contact details
    # contact_name = StringField(label='Name')
    # contact_email = EmailField(label='E-mail address')
    # contact_phone = TelField(label='Phone number')
    #
    # contact_2_name = StringField(label='Name')
    # contact_2_email = EmailField(label='E-mail address')
    # contact_2_phone = TelField(label='Phone number')
    #
    # def error_items(self):
    #     return self.errors.items()
    #
    # def get_other(self, field_name):
    #     return getattr(self, field_name+'_other')

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField, HiddenField, BooleanField
from wtforms.fields.html5 import DateField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional, ValidationError, InputRequired

from application.cms.models import TypeOfData


class TypeOfDataRequiredValidator:

    def __call__(self, form, field):
        message = 'Select at least one'
        administrative_data = form.data.get('administrative_data', False)
        survey_data = form.data.get('survey_data', False)
        if not administrative_data and not survey_data:
            raise ValidationError(message)


class FrequencyOtherRequiredValidator:

    def __call__(self, form, field):
        message = 'Other selected but no value has been entered'
        if form.frequency_of_release.data == 'other':
            if not form.frequency_of_release_other.data:
                form.errors['frequency_of_release_other'] = ['This should not be blank']
                raise ValidationError(message)


class PageForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    description = TextAreaField(label='description', validators=[DataRequired()])


class NewMeasurePageForm(FlaskForm):
    guid = StringField(label='ID', validators=[DataRequired()])
    title = StringField(label='Title', validators=[DataRequired()])


class MeasurePageForm(FlaskForm):

    def __init__(self, *args, **kwargs):

        super(MeasurePageForm, self).__init__(*args, **kwargs)
        choice_model = kwargs.get('frequency_of_release_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()

        self.frequency_of_release.choices = [(choice.key, choice.description) for choice in choices]

    guid = StringField(label='ID', validators=[DataRequired()])
    db_version_id = HiddenField()
    title = StringField(label='Title', validators=[DataRequired()])
    publication_date = DateField(label='Publication date', format='%Y-%m-%d', validators=[Optional()])
    time_covered = StringField(label='Time period covered')
    geographic_coverage = StringField(label='Area covered')
    lowest_level_of_geography = StringField(label='Lowest level of geography')

    # Primary source
    source_text = StringField(label='Title')
    department_source = StringField(label='Publisher')
    source_url = URLField(label='URL')
    published_date = StringField(label='Date first published')
    last_update_date = StringField(label='Date last updated')
    next_update_date = StringField(label='Next update')

    frequency_of_release = RadioField(label='Frequency of release',
                                      validators=[Optional(), FrequencyOtherRequiredValidator()])
    frequency_of_release_other = StringField(label='Other')

    type_of_statistic = StringField(label='Statistic type')
    contact_name = StringField(label='Name')
    contact_phone = StringField(label='Phone number')
    contact_email = StringField(label='E-mail address')
    suppression_rules = TextAreaField(label='Suppression rules')
    disclosure_control = TextAreaField(label='Disclosure control')

    primary_source_contact_2_name = StringField(label='Name')
    primary_source_contact_2_email = EmailField(label='E-mail address')
    primary_source_contact_2_phone = TelField(label='Phone number')

    # Secondary source 1
    secondary_source_1_title = StringField(label='Title')
    secondary_source_1_publisher = StringField(label='Publisher')
    secondary_source_1_url = URLField(label='URL')
    secondary_source_1_date = StringField(label='Date first published')
    secondary_source_1_date_updated = StringField(label='Date last updated')
    secondary_source_1_date_next_update = StringField(label='Next update')
    secondary_source_1_frequency = StringField(label='Frequency of release')
    secondary_source_1_statistic_type = StringField(label='Statistic type')
    secondary_source_1_suppression_rules = TextAreaField(label='Suppression rules')
    secondary_source_1_disclosure_control = TextAreaField(label='Disclosure control')
    secondary_source_1_contact_1_name = StringField(label='Name')
    secondary_source_1_contact_1_email = EmailField(label='E-mail address')
    secondary_source_1_contact_1_phone = TelField(label='Phone number')
    secondary_source_1_contact_2_name = StringField(label='Name')
    secondary_source_1_contact_2_email = EmailField(label='E-mail address')
    secondary_source_1_contact_2_phone = TelField(label='Phone number')

    # Secondary source 1
    secondary_source_2_title = StringField(label='Title')
    secondary_source_2_publisher = StringField(label='Publisher')
    secondary_source_2_url = URLField(label='URL')
    secondary_source_2_date = StringField(label='Date first published')
    secondary_source_2_date_updated = StringField(label='Date last updated')
    secondary_source_2_date_next_update = StringField(label='Next update')
    secondary_source_2_frequency = StringField(label='Frequency of release')
    secondary_source_2_statistic_type = StringField(label='Statistic type')
    secondary_source_2_suppression_rules = TextAreaField(label='Suppression rules')
    secondary_source_2_disclosure_control = TextAreaField(label='Disclosure control')
    secondary_source_2_contact_1_name = StringField(label='Name')
    secondary_source_2_contact_1_email = EmailField(label='E-mail address')
    secondary_source_2_contact_1_phone = TelField(label='Phone number')
    secondary_source_2_contact_2_name = StringField(label='Name')
    secondary_source_2_contact_2_email = EmailField(label='E-mail address')
    secondary_source_2_contact_2_phone = TelField(label='Phone number')

    # Commentary
    summary = TextAreaField(label='Main points')
    measure_summary = TextAreaField(label='What the data measures')
    need_to_know = TextAreaField(label='Things you need to know')
    ethnicity_definition_summary = TextAreaField(label='Why these ethnic categories were chosen')

    # Technical Details
    administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value)
    survey_data = BooleanField(label=TypeOfData.SURVEY.value)

    data_source_purpose = TextAreaField(label='Purpose of data source')
    methodology = TextAreaField(label='Methodology')
    estimation = TextAreaField(label='Rounding')
    related_publications = TextAreaField(label='Related publications')
    qmi_url = StringField(label='Quality Methodology Information link')
    further_technical_information = TextAreaField(label='Further technical information')

    # Edit summaries
    external_edit_summary = TextAreaField(label='External edit summary')
    internal_edit_summary = TextAreaField(label='Internal edit summary')

    def error_items(self):
        return self.errors.items()


class DimensionForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    time_period = StringField(label='Time Period')
    summary = TextAreaField(label='Summary')


class UploadForm(FlaskForm):
    guid = StringField()
    upload = FileField(label="File")
    title = StringField(label="Title", validators=[DataRequired()])
    description = TextAreaField()


class MeasurePageRequiredForm(MeasurePageForm):

    def __init__(self, *args, **kwargs):
        kwargs['meta'] = kwargs.get('meta') or {}
        super(MeasurePageRequiredForm, self).__init__(*args, **kwargs)

        choice_model = kwargs.get('frequency_of_release_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()

        self.frequency_of_release.choices = [(choice.key, choice.description) for choice in choices]

    time_covered = StringField(label='Time period covered', validators=[DataRequired()])
    geographic_coverage = StringField(label='Area covered', validators=[DataRequired()])
    lowest_level_of_geography = StringField(label='Lowest level of geography', validators=[DataRequired()])

    source_text = StringField(label='Title', validators=[DataRequired()])
    source_url = URLField(label='URL', validators=[DataRequired()])

    last_update_date = StringField(label='Date last updated', validators=[DataRequired()])
    measure_summary = TextAreaField(label='What the data measures',  validators=[DataRequired()])
    summary = TextAreaField(label='Main points',  validators=[DataRequired()])
    need_to_know = TextAreaField(label='Things you need to know', validators=[DataRequired()])
    ethnicity_definition_summary = TextAreaField(label='Why these ethnic categories were chosen',
                                                 validators=[DataRequired()])

    administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value,
                                       validators=[TypeOfDataRequiredValidator()])
    survey_data = BooleanField(label=TypeOfData.SURVEY.value,
                               validators=[TypeOfDataRequiredValidator()])

    frequency_of_release = RadioField(label='Frequency of release',
                                      validators=[InputRequired(message='Select one'),
                                                  FrequencyOtherRequiredValidator()])
    frequency_of_release_other = StringField(label='Other')

    data_source_purpose = TextAreaField(label='Purpose of data source', validators=[DataRequired()])
    methodology = TextAreaField(label='Methodology', validators=[DataRequired()])
    internal_edit_summary = StringField(label='Internal edit summary', validators=[DataRequired()])

    def error_items(self):
        items = self.errors.items()
        filtered = [item for item in items if item[0] != 'survey_data']
        return filtered


class DimensionRequiredForm(DimensionForm):
    def __init__(self, *args, **kwargs):
        kwargs['meta'] = kwargs.get('meta') or {}

        super(DimensionRequiredForm, self).__init__(*args, **kwargs)

    title = StringField(label='Title', validators=[DataRequired()])
    summary = TextAreaField(label='Summary', validators=[DataRequired()])


class NewVersionForm(FlaskForm):
    version_type = RadioField(label='New version type',
                              validators=[DataRequired()],
                              choices=[('minor', 'Minor'), ('major', 'Major')])

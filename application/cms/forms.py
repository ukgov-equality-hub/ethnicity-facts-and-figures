from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField, HiddenField, BooleanField
from wtforms.fields.html5 import DateField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Optional, ValidationError

from application.cms.models import TypeOfData, UKCountry


class TypeOfDataRequiredValidator:

    def __call__(self, form, field):
        administrative = form.data.get('administrative_data', False)
        survey = form.data.get('survey_data', False)

        if not any([administrative, survey]):
            raise ValidationError('Select at least one')


class AreaCoveredRequiredValidator:

    def __call__(self, form, field):
        england = form.data.get('england', False)
        wales = form.data.get('wales', False)
        scotland = form.data.get('scotland', False)
        northern_ireland = form.data.get('northern_ireland', False)

        if not any([england, wales, scotland, northern_ireland]):
            raise ValidationError('Select at least one')


class FrequencyOtherRequiredValidator:

    def __call__(self, form, field):
        message = 'Other selected but no value has been entered'
        if form.frequency_id.choices[form.frequency_id.data - 1][1].lower() == 'other':
            if not form.frequency_other.data:
                form.errors['frequency_other'] = ['This field is required']
                raise ValidationError(message)

        if form.secondary_source_1_frequency_id.data is not None:
            if form.secondary_source_1_frequency_id.choices[form.secondary_source_1_frequency_id.data - 1][1].lower() == 'other':  # noqa
                if not form.secondary_source_1_frequency_other.data:
                    form.errors['secondary_source_1_frequency_other'] = ['This field is required']
                    raise ValidationError(message)


class PageForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    description = TextAreaField(label='description', validators=[DataRequired()])


class MeasurePageForm(FlaskForm):

    def __init__(self, *args, **kwargs):

        super(MeasurePageForm, self).__init__(*args, **kwargs)
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

        choice_model = kwargs.get('lowest_level_of_geography_choices', None)
        choices = []
        if choice_model:
            geographic_choices = choice_model.query.order_by('position').all()
            for choice in geographic_choices:
                if choice.description is not None:
                    description = '%s %s' % (choice.name, choice.description)
                    choices.append((choice.name, description))
                else:
                    choices.append((choice.name, choice.name))

        self.lowest_level_of_geography_id.choices = choices

    db_version_id = HiddenField()
    title = StringField(label='Title', validators=[DataRequired()])
    internal_reference = StringField(label='Internal reference (optional)')
    publication_date = DateField(label='Publication date', format='%Y-%m-%d', validators=[Optional()])
    time_covered = StringField(label='Time period covered')

    england = BooleanField(label=UKCountry.ENGLAND.value)
    wales = BooleanField(label=UKCountry.WALES.value)
    scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)

    lowest_level_of_geography_id = RadioField(label='Lowest level of geography', validators=[Optional()])

    # Primary source
    source_text = StringField(label='Title of data source')

    # Type of data
    administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value)
    survey_data = BooleanField(label=TypeOfData.SURVEY.value)

    type_of_statistic_id = RadioField(label='Type of statistic', coerce=int, validators=[Optional()])

    department_source = StringField(label='Publisher')
    source_url = URLField(label='URL')
    published_date = StringField(label='Publication release date')
    note_on_corrections_or_updates = TextAreaField(label='Note on corrections or updates')
    frequency_id = RadioField(label='Publication frequency',
                              coerce=int,
                              validators=[Optional(), FrequencyOtherRequiredValidator()])
    frequency_other = StringField(label='Other')

    data_source_purpose = TextAreaField(label='Purpose of data source')
    suppression_and_disclosure = TextAreaField(label='Suppression rules and disclosure control')
    estimation = TextAreaField(label='Rounding')

    # End primary source

    # Secondary source
    secondary_source_1_title = StringField(label='Title of data source')

    # Secondary source type of data
    secondary_source_1_administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value)
    secondary_source_1_survey_data = BooleanField(label=TypeOfData.SURVEY.value)

    secondary_source_1_type_of_statistic_id = RadioField(label='Type of statistic', coerce=int,
                                                         validators=[Optional()])

    secondary_source_1_publisher = StringField(label='Publisher')

    secondary_source_1_url = URLField(label='URL')
    secondary_source_1_date = StringField(label='Publication release date')
    secondary_source_1_note_on_corrections_or_updates = TextAreaField(label='Note on corrections or updates')
    secondary_source_1_frequency_id = RadioField(label='Publication frequency',
                                                 coerce=int,
                                                 validators=[Optional(), FrequencyOtherRequiredValidator()])
    secondary_source_1_frequency_other = StringField(label='Other')

    secondary_source_1_data_source_purpose = TextAreaField(label='Purpose of data source')
    secondary_source_1_suppression_and_disclosure = TextAreaField(label='Suppression rules and disclosure control')
    secondary_source_1_estimation = TextAreaField(label='Rounding')

    # End secondary source

    # Commentary
    summary = TextAreaField(label='Main points')
    measure_summary = TextAreaField(label='What the data measures')
    need_to_know = TextAreaField(label='Things you need to know')
    ethnicity_definition_summary = TextAreaField(label='The ethnic categories used in this data')

    methodology = TextAreaField(label='Methodology')
    related_publications = TextAreaField(label='Related publications')
    qmi_url = StringField(label='Quality Methodology Information URL')
    further_technical_information = TextAreaField(label='Further technical information')

    # Edit summaries
    external_edit_summary = TextAreaField(label='External edit summary')
    internal_edit_summary = TextAreaField(label='Internal edit summary')

    # Contact details
    contact_name = StringField(label='Name')
    contact_email = EmailField(label='E-mail address')
    contact_phone = TelField(label='Phone number')

    contact_2_name = StringField(label='Name')
    contact_2_email = EmailField(label='E-mail address')
    contact_2_phone = TelField(label='Phone number')

    def error_items(self):
        return self.errors.items()

    def get_other(self, field_name):
        return getattr(self, field_name+'_other')


class DimensionForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    time_period = StringField(label='Time Period')
    summary = TextAreaField(label='Summary')
    ethnicity_category = StringField(label='Ethnicity categorisation')
    include_parents = BooleanField(label='Values for broad ethnic groups shown')
    include_all = BooleanField(label='Values for ‘All’ ethnicities shown')
    include_unknown = BooleanField(label='Values for ‘Unknown’ ethnicities shown')

    def __init__(self, *args, **kwargs):
        super(FlaskForm, self).__init__(*args, **kwargs)


class UploadForm(FlaskForm):
    guid = StringField()
    upload = FileField(label="File")
    title = StringField(label="Title", validators=[DataRequired()])
    description = TextAreaField()


class MeasurePageRequiredForm(MeasurePageForm):

    def __init__(self, *args, **kwargs):
        kwargs['meta'] = kwargs.get('meta') or {}
        super(MeasurePageRequiredForm, self).__init__(*args, **kwargs)

        choice_model = kwargs.get('frequency_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()

        self.frequency_id.choices = [(choice.id, choice.description) for choice in choices]

        choice_model = kwargs.get('type_of_statistic_choices', None)
        choices = []
        if choice_model:
            choices = choice_model.query.order_by('position').all()
        self.type_of_statistic_id.choices = [(choice.id, choice.internal) for choice in choices]

        choice_model = kwargs.get('lowest_level_of_geography_choices', None)
        choices = []
        if choice_model:
            geographic_choices = choice_model.query.order_by('position').all()
            for choice in geographic_choices:
                if choice.description is not None:
                    description = '%s %s' % (choice.name, choice.description)
                    choices.append((choice.name, description))
                else:
                    choices.append((choice.name, choice.name))
        self.lowest_level_of_geography_id.choices = choices

    time_covered = StringField(label='Time period covered', validators=[DataRequired()])

    england = BooleanField(label=UKCountry.ENGLAND.value, validators=[AreaCoveredRequiredValidator()])
    wales = BooleanField(label=UKCountry.WALES.value)
    scotland = BooleanField(label=UKCountry.SCOTLAND.value)
    northern_ireland = BooleanField(label=UKCountry.NORTHERN_IRELAND.value)

    lowest_level_of_geography_id = RadioField(label='Lowest level of geography',
                                              validators=[DataRequired(message='Select one')])

    department_source = StringField(label='Publisher', validators=[DataRequired()])
    source_text = StringField(label='Title', validators=[DataRequired()])
    source_url = URLField(label='URL', validators=[DataRequired()])

    measure_summary = TextAreaField(label='What the data measures',  validators=[DataRequired()])
    summary = TextAreaField(label='Main points',  validators=[DataRequired()])
    need_to_know = TextAreaField(label='Things you need to know', validators=[DataRequired()])
    ethnicity_definition_summary = TextAreaField(label='The ethnic categories used in this data',
                                                 validators=[DataRequired()])

    administrative_data = BooleanField(label=TypeOfData.ADMINISTRATIVE.value,
                                       validators=[TypeOfDataRequiredValidator()])
    survey_data = BooleanField(label=TypeOfData.SURVEY.value,
                               validators=[TypeOfDataRequiredValidator()])

    frequency_id = RadioField(label='Frequency of release',
                              coerce=int,
                              validators=[DataRequired(message='Select one'), FrequencyOtherRequiredValidator()])
    frequency_other = StringField(label='Other')

    type_of_statistic_id = RadioField(label='Type of statistic', coerce=int, validators=[DataRequired('Select one')])

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


class NewCategoryForm(FlaskForm):
    family = StringField(label='Family (e.g. Ethnicity)', validators=[DataRequired()])
    subfamily = StringField(label='Subfamily (e.g. Common Ethnicities)', validators=[DataRequired()])
    position = StringField(label='Position in family')
    title = StringField(label='Title (e.g ONS Broad Ethnicities)', validators=[DataRequired()])


class NewValuesForm(FlaskForm):
    value1 = StringField(label='Value 1')
    value2 = StringField(label='Value 2')
    value3 = StringField(label='Value 3')
    value4 = StringField(label='Value 4')
    value5 = StringField(label='Value 5')

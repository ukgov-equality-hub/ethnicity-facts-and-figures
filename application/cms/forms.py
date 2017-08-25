from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, RadioField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Optional


class PageForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    description = TextAreaField(label='description', validators=[DataRequired()])


class MeasurePageForm(FlaskForm):
    # TODO: Ensure ID is unique
    guid = StringField(label='ID')
    title = StringField(label='Title')
    publication_date = DateField(label='Publication date', format='%Y-%m-%d', validators=[Optional()])
    time_covered = StringField(label='Time covered')
    geographic_coverage = StringField(label='Geographic coverage')
    lowest_level_of_geography = StringField(label='Lowest level of geography')

    # Source details
    source_text = StringField(label='Source')
    source_url = StringField(label='Source link')
    department_source = StringField(label='Department source')
    published_date = StringField(label='Date measure was first published')
    last_update_date = StringField(label='Date publication was last updated')
    next_update_date = StringField(label='Next update')
    frequency = StringField(label='Frequency of release')
    type_of_statistic = StringField(label='Type of statistic')
    suppression_rules = TextAreaField(label='Suppression rules')
    disclosure_control = TextAreaField(label='Disclosure control')
    contact_name = StringField(label='Contact name')
    contact_phone = StringField(label='Contact phone')
    contact_email = StringField(label='Contact email')

    # Commentary
    summary = TextAreaField(label='Main points')
    need_to_know = TextAreaField(label='Things you need to know')
    measure_summary = TextAreaField(label='What the data measures')
    ethnicity_definition_summary = TextAreaField(label='Why these ethnic categories were chosen')
    # ethnicity_definition_detail = TextAreaField(label='Further information')

    # Technical Details
    data_type = StringField(label='Type of data')
    data_source_purpose = TextAreaField(label='Purpose of data source')
    methodology = TextAreaField(label='Methodology')
    estimation = TextAreaField(label='Rounding')
    related_publications = StringField(label='Related publications')

    # Quality assurance and validation
    qmi_url = StringField(label='Quality Methodology Information link')
    further_technical_information = TextAreaField(label='Further technical information')

    external_edit_summary = TextAreaField(label='External edit summary')
    internal_edit_summary = TextAreaField(label='Internal edit summary')


class DimensionForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    time_period = StringField(label='Time Period')
    summary = TextAreaField(label='Summary')


class UploadForm(FlaskForm):
    guid = StringField()
    upload = FileField()
    title = StringField(label="File name")
    description = TextAreaField()


class MeasurePageRequiredForm(MeasurePageForm):
    def __init__(self, *args, **kwargs):
        kwargs['meta'] = kwargs.get('meta') or {}
        kwargs['meta'].setdefault('csrf', False)

        super(MeasurePageRequiredForm, self).__init__(*args, **kwargs)

    measure_summary = TextAreaField(label='Measure explanation',  validators=[DataRequired()])
    summary = TextAreaField(label='Main points',  validators=[DataRequired()])
    geographic_coverage = TextAreaField(label='Geographic coverage', validators=[DataRequired()])
    lowest_level_of_geography = TextAreaField(label='Lowest level of geography', validators=[DataRequired()])
    time_covered = TextAreaField(label='Time covered', validators=[DataRequired()])
    need_to_know = TextAreaField(label='Things you need to know', validators=[DataRequired()])
    ethnicity_definition_summary = TextAreaField(label='Ethnicity categories used in this analysis',
                                                 validators=[DataRequired()])
    source_text = TextAreaField(label='Source', validators=[DataRequired()])
    source_url = StringField(label='Source link', validators=[DataRequired()])
    last_update_date = StringField(label='Date publication was last updated', validators=[DataRequired()])
    data_source_purpose = TextAreaField(label='Purpose of data source', validators=[DataRequired()])
    methodology = TextAreaField(label='Methodology', validators=[DataRequired()])
    data_type = StringField(label='Type of data', validators=[DataRequired()])


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

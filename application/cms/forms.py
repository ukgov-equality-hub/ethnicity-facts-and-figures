from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class PageForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    description = TextAreaField(label='description', validators=[DataRequired()])


class MeasurePageForm(FlaskForm):
    # TODO: Ensure ID is unique
    guid = StringField(label='ID')
    title = StringField(label='Title')
    # Overview
    measure_summary = TextAreaField(label='Measure explanation')
    summary = TextAreaField(label='Main points')
    geographic_coverage = TextAreaField(label='Geographic coverage')
    lowest_level_of_geography = TextAreaField(label='Lowest level of geography')
    time_covered = TextAreaField(label='Time covered')
    # Need To Know
    need_to_know = TextAreaField(label='Things you need to know')
    ethnicity_definition_summary = TextAreaField(label='Ethnicity categories used in this analysis')
    ethnicity_definition_detail = TextAreaField(label='Further information')
    # Publishing Details
    source_text = TextAreaField(label='Source')
    source_url = StringField(label='Source link')
    department_source = TextAreaField(label='Department source')
    published_date = StringField(label='Date measure was first published')
    last_update_date = StringField(label='Date publication was last updated')
    next_update_date = StringField(label='Next update')
    frequency = StringField(label='Frequency of release')
    related_publications = TextAreaField(label='Related publications')
    contact_name = StringField(label='Contact name')
    contact_phone = StringField(label='Contact phone')
    contact_email = StringField(label='Contact email')
    # Technical Details
    data_source_purpose = TextAreaField(label='Purpose of data source')
    methodology = TextAreaField(label='Methodology')
    data_type = StringField(label='Type of data')
    suppression_rules = TextAreaField(label='Suppression rules')
    disclosure_control = TextAreaField(label='Disclosure control')
    estimation = TextAreaField(label='Rounding')
    # Quality assurance and validation
    qmi_url = StringField(label='Quality information and methodology link')
    further_technical_information = TextAreaField(label='Further technical information')


class DimensionForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    time_period = StringField(label='Time Period')
    summary = TextAreaField(label='Summary')
    suppression_rules = TextAreaField(label='Suppression Rules')
    disclosure_control = TextAreaField(label='Disclosure control')
    type_of_statistic = StringField(label='Type of statistic')
    location = StringField(label='Location')
    source = StringField(label='Source')


class MeasurePageRequiredForm(MeasurePageForm):
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
    title = StringField(label='Title', validators=[DataRequired()])
    summary = TextAreaField(label='Summary', validators=[DataRequired()])
    source = StringField(label='Source', validators=[DataRequired()])

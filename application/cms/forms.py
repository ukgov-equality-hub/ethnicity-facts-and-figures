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
    measure_summary = TextAreaField(label='Measure information')
    summary = TextAreaField(label='Summary')
    geographic_coverage = StringField(label='Geographic coverage')
    time_covered = TextAreaField(label='Time covered')
    keywords = StringField(label='keywords')
    # Need To Know
    need_to_know = TextAreaField(label='Need to know')
    ethnicity_definition_summary = TextAreaField(label='Ethnicity definition - summary')
    ethnicity_definition_detail = TextAreaField(label='Ethnicity definition - detail')
    location_definition_summary = TextAreaField(label='Location Definition - summary')
    location_definition_detail = TextAreaField(label='Location Definition - detail')
    # Publishing Details
    source_text = TextAreaField(label='Source text')
    source_url = StringField(label='Source url')
    department_source = TextAreaField(label='Source (department)')
    published_date = StringField(label='Published date')
    last_update_date = StringField(label='Last updated')
    revisions = StringField(label='Revisions')  # I believe this should be an array
    next_update_date = StringField(label='Next update')
    frequency = StringField(label='Frequency')
    # related_publications = array
    contact_name = StringField(label='Contact name')
    contact_phone = StringField(label='Contact phone')
    contact_email = StringField(label='Contact email')
    # Technical Details
    methodology = TextAreaField(label='Methodology')
    data_type = StringField(label='Data type')
    population_or_sample = TextAreaField(label='Population or sample')
    disclosure_control = TextAreaField(label='Disclosure control')
    estimation = TextAreaField(label='Estimation/Rounding')
    # Quality assurance and validation
    quality_assurance = TextAreaField(label='Quality Assurance')
    qmi_text = TextAreaField(label='Quality information and methodology (QMI) statement')
    qmi_url = StringField(label='QMI URL')
    # analyses - TODO


class DimensionForm(FlaskForm):
    title = StringField(label='Title', validators=[DataRequired()])
    time_period = StringField(label='Time Period', validators=[DataRequired()])
    summary = TextAreaField(label='Summary', validators=[DataRequired()])

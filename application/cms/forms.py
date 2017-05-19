from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class PageForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    description = TextAreaField(label='description', validators=[DataRequired()])


class MeasurePageForm(FlaskForm):
    # TODO: Ensure ID is unique
    guid = StringField(label='ID', validators=[DataRequired()])
    title = StringField(label='Title', validators=[DataRequired()])
    # Overview
    measure_summary = TextAreaField(label='Measure information', validators=[DataRequired()])
    summary = TextAreaField(label='Summary', validators=[DataRequired()])
    geographic_coverage = StringField(label='Geographic coverage', validators=[DataRequired()])
    time_covered = TextAreaField(label='Time covered', validators=[DataRequired()])
    keywords = StringField(label='keywords', validators=[DataRequired()])
    # Need To Know
    need_to_know = TextAreaField(label='Need to know', validators=[DataRequired()])
    ethnicity_definition_summary = TextAreaField(label='Ethnicity definition - summary', validators=[DataRequired()])
    ethnicity_definition_detail = TextAreaField(label='Ethnicity definition - detail', validators=[DataRequired()])
    location_definition_summary = TextAreaField(label='Location Definition - summary', validators=[DataRequired()])
    location_definition_detail = TextAreaField(label='Location Definition - detail', validators=[DataRequired()])
    # Publishing Details
    source_text = TextAreaField(label='Source text', validators=[DataRequired()])
    source_url = StringField(label='Source url', validators=[DataRequired()])
    department_source = TextAreaField(label='Source (department)', validators=[DataRequired()])
    published_date = StringField(label='Published date', validators=[DataRequired()])
    last_update_date = StringField(label='Last updated', validators=[DataRequired()])
    revisions = StringField(label='Revisions')  # I believe this should be an array
    next_update_date = StringField(label='Next update')
    frequency = StringField(label='Frequency', validators=[DataRequired()])
    # related_publications = array
    contact_name = StringField(label='Contact name', validators=[DataRequired()])
    contact_phone = StringField(label='Contact phone')
    contact_email = StringField(label='Contact email')
    # Technical Details
    methodology = TextAreaField(label='Methodology', validators=[DataRequired()])
    data_type = StringField(label='Data type', validators=[DataRequired()])
    population_or_sample = TextAreaField(label='Population or sample', validators=[DataRequired()])
    disclosure_control = TextAreaField(label='Disclosure control', validators=[DataRequired()])
    estimation = TextAreaField(label='Estimation/Rounding', validators=[DataRequired()])
    # Quality assurance and validation
    quality_assurance = TextAreaField(label='Quality Assurance', validators=[DataRequired()])
    qmi_text = TextAreaField(label='Quality information and methodology (QMI) statement', validators=[DataRequired()])
    qmi_url = StringField(label='QMI URL', validators=[DataRequired()])
    # analyses - TODO

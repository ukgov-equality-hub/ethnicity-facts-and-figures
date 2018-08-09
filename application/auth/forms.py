from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired()])
    # TODO ? validation error if not gov.uk email?

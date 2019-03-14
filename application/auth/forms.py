from flask_security.forms import LoginForm as FlaskSecurityLoginForm, password_required, Required
from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from application.cms.form_fields import RDUStringField, RDUPasswordField


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired()])
    # TODO ? validation error if not gov.uk email?


class LoginForm(FlaskSecurityLoginForm):
    email = RDUStringField("Email", validators=[Required(message="EMAIL_NOT_PROVIDED")])
    password = RDUPasswordField("Password", validators=[password_required])

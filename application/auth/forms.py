from flask_security.forms import LoginForm as FlaskSecurityLoginForm, Required
from flask_security.utils import verify_password
from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from application.form_fields import RDUStringField, RDUPasswordField


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email address", validators=[DataRequired()])
    # TODO ? validation error if not gov.uk email?


class LoginForm(FlaskSecurityLoginForm):
    email = RDUStringField("Email", validators=[Required(message="Enter your email address")])
    password = RDUPasswordField("Password", validators=[Required(message="Enter your password")])

    def validate(self):
        result = super().validate()

        # Check for parent form's processing and override messaging so that we don't leak the existence of a specific
        # account, which Flask-Security does by default. `user` attribute is only set if the initial validators pass,
        # i.e. both fields have data.
        if result is False and hasattr(self, "user"):
            if not self.user or not self.user.password or not verify_password(self.password.data, self.user.password):
                self.email.errors = ["Check your email address"]
                self.password.errors = ["Check your password"]

        return result

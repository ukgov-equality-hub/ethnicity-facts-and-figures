from flask_security.forms import LoginForm as FlaskSecurityLoginForm, Required
from flask_security.utils import verify_password
from flask_wtf import FlaskForm, RecaptchaField
from wtforms.validators import DataRequired, Email

from application.form_fields import RDUStringField, RDUPasswordField, RDUEmailField, ValidPublisherEmailAddress


class ForgotPasswordForm(FlaskForm):
    email = RDUEmailField(
        "Email address",
        hint="Enter the email address you login with",
        validators=[
            DataRequired(message="Enter an email address"),
            Email(message="Enter a valid email address"),
            ValidPublisherEmailAddress(),
        ],
    )
    recaptcha = RecaptchaField("ReCaptcha", validators=[Required(message="Enter all required details")])

    def validate(self):
        result = super().validate()

        if result is False:
            self.email.errors = ["Check your email address"]
        return result


class LoginForm(FlaskSecurityLoginForm):
    email = RDUStringField("Email", validators=[Required(message="Enter your email address")])
    password = RDUPasswordField("Password", validators=[Required(message="Enter your password")])
    recaptcha = RecaptchaField("ReCaptcha", validators=[Required(message="Enter all required details")])

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

import re
import os
import ast

from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.fields.html5 import EmailField
from wtforms.validators import Length, DataRequired, Email

from application.cms.form_fields import RDURadioField


whitelist = ast.literal_eval(os.environ.get("ACCOUNT_WHITELIST", "[]"))


class ValidGovEmail:
    def __call__(self, form, field):
        message = "Enter a government email address"
        if not is_gov_email(field.data.lower()):
            raise ValidationError(message)


def email_address(label="Email address", **kwargs):

    validators = [
        Length(min=5, max=255),
        DataRequired(message="Can’t be empty"),
        Email(message="Enter a valid email address"),
        ValidGovEmail(),
    ]

    return EmailField(label, validators)


def is_gov_email(email):
    email = email.lower()
    if email in whitelist:
        return True
    valid_domains = [r"gov\.uk|nhs\.net"]
    email_regex = r"[\.|@]({})$".format("|".join(valid_domains))
    return bool(re.search(email_regex, email))


class AddUserForm(FlaskForm):
    email = email_address()
    user_type = RDURadioField(
        label="What type of user account?",
        choices=[("RDU_USER", "RDU CMS user"), ("DEPT_USER", "Departmental CMS user"), ("DEV_USER", "RDU Developer")],
        default="RDU_USER",
        validators=[DataRequired()],
    )

import re

from flask_wtf import FlaskForm
from wtforms import ValidationError, RadioField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Length, DataRequired, Email


def email_address(label='Email address', **kwargs):

    # TODO before merge to master add valid gov email validator
    # validators = [Length(min=5, max=255),
    #               DataRequired(message='Can’t be empty'),
    #               Email(message='Enter a valid email address'),
    #               ValidGovEmail()]

    validators = [Length(min=5, max=255),
                  DataRequired(message='Can’t be empty'),
                  Email(message='Enter a valid email address')]

    return EmailField(label, validators)


def is_gov_user(email_address):
    valid_domains = [r'gov\.uk']
    email_regex = (r"[\.|@]({})$".format("|".join(valid_domains)))
    return bool(re.search(email_regex, email_address.lower()))


class AddUserForm(FlaskForm):
    email = email_address()
    user_type = RadioField('User type',
                           choices=[('INTERNAL_USER', 'RDU CMS user'), ('DEPARTMENTAL_USER', 'Departmental CMS user')],
                           default='INTERNAL_USER',
                           validators=[DataRequired()])


class ValidGovEmail:

    def __call__(self, form, field):
        message = 'Enter a government email address.'
        if not is_gov_user(field.data.lower()):
            raise ValidationError(message)

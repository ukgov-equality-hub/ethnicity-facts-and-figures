from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Email

from application.form_fields import RDURadioField, RDUEmailField, ValidPublisherEmailAddress, RDUSearchField


class AddUserForm(FlaskForm):
    email = RDUEmailField(
        label="Email address",
        validators=[
            Length(min=5, max=255),
            DataRequired(message="Enter an email address"),
            Email(message="Enter a valid email address"),
            ValidPublisherEmailAddress(),
        ],
    )
    user_type = RDURadioField(
        label="What type of user account?",
        choices=[("RDU_USER", "RDU CMS user"), ("DEPT_USER", "Departmental CMS user"), ("DEV_USER", "RDU Developer")],
        default="RDU_USER",
        validators=[DataRequired()],
    )


class DataSourceSearchForm(FlaskForm):

    q = RDUSearchField(label="Search")

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Email

from application.form_fields import RDURadioField, RDUEmailField, ValidGovEmail


class AddUserForm(FlaskForm):
    email = RDUEmailField(
        label="Email address",
        validators=[
            Length(min=5, max=255),
            DataRequired(message="Can’t be empty"),
            Email(message="Enter a valid email address"),
            ValidGovEmail(),
        ],
    )
    user_type = RDURadioField(
        label="What type of user account?",
        choices=[("RDU_USER", "RDU CMS user"), ("DEPT_USER", "Departmental CMS user"), ("DEV_USER", "RDU Developer")],
        default="RDU_USER",
        validators=[DataRequired()],
    )

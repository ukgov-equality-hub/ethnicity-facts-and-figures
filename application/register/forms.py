from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, EqualTo

from application.form_fields import RDUPasswordField


class SetPasswordForm(FlaskForm):
    password = RDUPasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter a password"),
            Length(min=10, max=50, message="Passwords must be between 10 and 50 characters"),
        ],
    )

    confirm_password = RDUPasswordField(
        "Confirm password",
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo("password", message="The passwords you entered do not match"),
        ],
    )

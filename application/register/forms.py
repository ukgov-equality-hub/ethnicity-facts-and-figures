from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import DataRequired, Length, EqualTo


class SetPasswordForm(FlaskForm):

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter a password"),
            Length(min=10, max=50, message="Passwords must be between 10 and 50 characters"),
        ],
    )

    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(message="Please confirm your new password"),
            EqualTo("password", message="The passwords you entered do not match"),
        ],
    )

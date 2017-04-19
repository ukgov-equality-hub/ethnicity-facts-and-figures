from flask_wtf import FlaskForm
from wtforms import validators
from wtforms.fields.html5 import EmailField


class LoginForm(FlaskForm):
    email = EmailField(label='Admin', validators=[validators.DataRequired()])
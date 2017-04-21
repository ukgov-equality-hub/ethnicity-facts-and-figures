from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField


class LoginForm(FlaskForm):
    email = EmailField(label='email', validators=[DataRequired()])

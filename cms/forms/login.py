from flask_wtf import Form
from wtforms import StringField
from wtforms import validators

from auth.user import User
from auth.logins import usernames


class LoginForm(Form):
    email = StringField('Admin', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        email = self.data['email']
        if email in usernames:
            user = User(email=email)
            self.user = user
            return True
        else:
            self.email.errors.append('Unknown email')
            return False



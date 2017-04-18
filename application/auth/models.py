from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, email):
        self.id = email

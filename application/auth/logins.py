from application.auth.models import User

usernames = [
    'test@example.com',
]


def get_user(email):
    if email in usernames:
        return User(email=email)
    return None

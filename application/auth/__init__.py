from flask import Blueprint
from flask_login import LoginManager
from application.auth.models import User


login_manager = LoginManager()
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(email):
    user = User(email=email)
    return user


auth_blueprint = Blueprint('auth', __name__,  url_prefix='/auth')

from application.auth.views import (
    login,
    logout_user
)  # noqa
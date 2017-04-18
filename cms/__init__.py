from flask import Flask
from flask_login import LoginManager

from auth.user import User
from cms.views import cms

login_manager = LoginManager()

application = Flask(__name__)
application.register_blueprint(cms)
application.secret_key = '8zqLL28XKEuR$ntYYjhs*zqLL28XKEuR&ntYYjhs'

login_manager.init_app(application)
login_manager.login_view = "cms.login"

@login_manager.user_loader
def load_user(email):
    user = User(email=email)
    return user

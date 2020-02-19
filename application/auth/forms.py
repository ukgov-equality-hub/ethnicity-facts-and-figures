from flask_security.forms import LoginForm as FlaskSecurityLoginForm, Required
from flask_security.utils import verify_password, hash_password
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from application.form_fields import RDUStringField, RDUPasswordField, RDUEmailField, ValidPublisherEmailAddress

from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from application import db
from application.auth.models import UserAttemptedToLogin
from application.utils import send_reactivation_email
from flask import request, current_app
from math import exp
import time

import requests
import threading

thread_local = threading.local()


class ForgotPasswordForm(FlaskForm):
    email = RDUEmailField(
        "Email address",
        hint="Enter the email address you login with",
        validators=[
            DataRequired(message="Enter an email address"),
            Email(message="Enter a valid email address"),
            ValidPublisherEmailAddress(),
        ],
    )


class LoginForm(FlaskSecurityLoginForm):
    email = RDUStringField("Email", validators=[Required(message="Enter your email address")])
    password = RDUPasswordField("Password", validators=[Required(message="Enter your password")])

    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()

    def validate(self):
        result = super().validate()

        # Check for parent form's processing and override messaging so that we don't leak the existence of a specific
        # account, which Flask-Security does by default. `user` attribute is only set if the initial validators pass,
        # i.e. both fields have data.
        if result is False and self.user and hasattr(self, "user"):
            self.usernameFailedLogin(self)
        elif result is False:
            # user does not exist so check if email or password used exist in invalid user
            self.handleFailedLogin(self)

        if (
            not self.user
            or not self.user.active
            or not self.user.password
            or not verify_password(self.password.data, self.user.password)
        ):
            self.email.errors = ["Check your email address"]
            self.password.errors = ["Check your password"]
        elif result is True:
            # reset failed login attempts
            self.user.failed_login_count = 0
            db.session.commit()

        return result

    @staticmethod
    def usernameFailedLogin(self):
        if self.user.failed_login_count:
            self.user.failed_login_count += 1
        else:
            self.user.failed_login_count = 1

        # deactivate user if fails to login and send user an email
        if self.user.failed_login_count >= 3:
            self.user.active = False
            send_reactivation_email(self.user.email, current_app)

        db.session.commit()

        # throttle
        t1 = threading.Thread(target=self.throttle(self.user.failed_login_count))
        t1.start()

    @staticmethod
    def handleFailedLogin(self):
        try:
            invalidUser = UserAttemptedToLogin.query.filter_by(email=self.email.data.strip()).all()
            if invalidUser:
                maxFailures = 1
                for user in invalidUser:
                    if user.failed_login_count:
                        user.failed_login_count += 1
                    else:
                        user.failed_login_count = 1

                    if user.failed_login_count >= maxFailures:
                        maxFailures = user.failed_login_count
                # throttle
                t1 = threading.Thread(target=self.throttle(maxFailures))
                t1.start()

            else:
                # New invalid user, add invalid logins
                invalidUser = UserAttemptedToLogin(email=self.email)
                invalidUser.email = self.email.data.strip()
                invalidUser.password = hash_password(self.password.data.strip())
                invalidUser.ip = request.environ.get("REMOTE_ADDR")
                invalidUser.failed_login_count = 1

                db.session.add(invalidUser)

                # throttle
                t1 = threading.Thread(target=self.throttle(invalidUser.failed_login_count))
                t1.start()

            db.session.commit()
        except (MultipleResultsFound, NoResultFound) as e:
            current_app.logger.error(e)

    @staticmethod
    def throttle(number):
        time.sleep(exp(number))

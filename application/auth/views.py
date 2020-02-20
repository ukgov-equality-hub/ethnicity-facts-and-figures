import passwordmeter
from flask import render_template, flash, redirect, url_for, current_app, abort, session
from flask_mail import Message
from flask_security.decorators import anonymous_user_required
from flask_security.utils import hash_password
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from application.auth import auth_blueprint
from application.auth.forms import ForgotPasswordForm
from application import mail, db
from application.auth.models import User
from application.register.forms import SetPasswordForm
from application.utils import generate_token, check_token
from password_strength import PasswordStats


@auth_blueprint.route("/forgot", methods=["GET", "POST"])
@anonymous_user_required
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():

        email = form.email.data.strip()
        try:
            User.query.filter_by(email=email).one()
        except (MultipleResultsFound, NoResultFound) as e:
            current_app.logger.error(e)
            flash("Instructions for updating your password have been sent to %s" % email)
            return redirect(url_for("auth.forgot_password"))

        token = generate_token(email, current_app)
        confirmation_url = url_for("auth.reset_password", token=token, _external=True)

        html = render_template("auth/email/reset_instructions.html", confirmation_url=confirmation_url)

        msg = Message(
            html=html,
            subject="Password reset for the Ethnicity Facts and Figures content management system",
            sender=current_app.config["RDU_EMAIL"],
            recipients=[form.email.data],
        )
        try:
            mail.send(msg)
            flash("Instructions for updating your password have been sent to %s" % email)

        except Exception as ex:
            flash("Failed to send password reset email to: %s" % email, "error")
            current_app.logger.error(ex)

        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html", form=form)


@auth_blueprint.route("/reset/<token>", methods=["GET", "POST"])
@anonymous_user_required
def reset_password(token):
    email = check_token(token, current_app)
    if not email:
        current_app.logger.info("token has expired.")
        flash("Link has expired", "error")
        abort(400)

    form = SetPasswordForm()
    user = User.query.filter_by(email=email).first()

    if not user:
        return redirect(url_for("auth.login"))

    if form.validate_on_submit():
        password = form.password.data.strip()

        meter = passwordmeter.Meter(settings=dict(factors="length,variety,phrase,notword,casemix"))
        strength, improvements = meter.test(password)
        stats = PasswordStats(password)
        if strength < 0.7 or stats.length < 10 or stats.sequences_length > 1 or stats.weakness_factor:
            flash(
                """Your password is too weak. It has to be at least 10 characters long and use a mix of numbers, special
 characters as well as upper and lowercase letters. Avoid using common patterns and repeated characters.""",
                "error",
            )
            return render_template("auth/reset_password.html", form=SetPasswordForm(), token=token, user=user)

        user.password = hash_password(password)

        db.session.commit()

        # TODO send email notification of password reset?

        return render_template("auth/password_updated.html", form=form, token=token, user=user)

    return render_template("auth/reset_password.html", form=form, token=token, user=user)


@auth_blueprint.route("/logout", methods=["POST"])
def logout():
    session.clear()
    from flask_security.views import logout as security_logout_view

    return security_logout_view()

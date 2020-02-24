import datetime
import passwordmeter

from flask import current_app, flash, abort, render_template, redirect, url_for
from flask_security.decorators import anonymous_user_required
from flask_security.utils import hash_password

from application import db
from application.auth.models import User
from application.register import register_blueprint
from application.register.forms import SetPasswordForm
from application.utils import check_token
from password_strength import PasswordStats


@register_blueprint.route("/confirm-account/<token>", methods=["GET", "POST"])
@anonymous_user_required
def confirm_account(token):
    email = check_token(token, current_app)
    if not email:
        current_app.logger.info("token has expired.")
        flash("Link has expired", "error")
        abort(400)

    form = SetPasswordForm()
    user = User.query.filter_by(email=email).first()

    if not user:
        abort(404)

    if user.active:
        flash("Account already confirmed and password set")
        return redirect(url_for("register.completed", user_email=user.email))

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
            return render_template("register/set_account_password.html", form=SetPasswordForm(), token=token, user=user)

        user.active = True
        user.password = hash_password(password)
        user.confirmed_at = datetime.datetime.utcnow()

        db.session.commit()

        return redirect(url_for("register.completed", user_email=user.email))

    return render_template("register/set_account_password.html", form=form, token=token, user=user)


@register_blueprint.route("/completed/<user_email>")
@anonymous_user_required
def completed(user_email):
    user = User.query.filter_by(email=user_email).one()
    if user.is_departmental_user():
        return render_template("register/completed_departmental.html", user=user)
    else:
        return render_template("register/completed_internal.html", user=user)

import datetime
import passwordmeter

from flask import current_app, flash, abort, render_template, redirect, url_for
from flask_security.utils import encrypt_password

from application import db
from application.auth.models import User
from application.register import register_blueprint
from application.register.forms import SetPasswordForm
from application.utils import _check_token


@register_blueprint.route("/confirm-account/<token>", methods=['GET', 'POST'])
def confirm_account(token):
    email = _check_token(token, current_app)
    if not email:
        current_app.logger.info('token has expired.')
        flash('Link has expired', 'error')
        abort(400)

    form = SetPasswordForm()
    user = User.query.filter_by(email=email).first()

    if user.active:
        flash('Account already confirmed and password set')
        return 'Account already confirmed and password set'

    if form.validate_on_submit():
        password = form.password.data.strip()

        meter = passwordmeter.Meter(settings=dict(factors='charmix'))
        strength, improvements = meter.test(password)
        if strength < 0.7:
            message = ['Your password is too weak.']
            for key, val in improvements.items():
                message.append(val)

            flash('\n'.join(message), 'error')
            return render_template('register/set_account_password.html',
                                   form=SetPasswordForm(),
                                   token=token,
                                   user=user)

        user.active = True
        user.password = encrypt_password(password)
        user.confirmed_at = datetime.datetime.utcnow()

        db.session.add(user)
        db.session.commit()

        flash('Your account has been setup')
        return redirect(url_for('register.completed', user_email=user.email))

    return render_template('register/set_account_password.html',
                           form=form,
                           token=token,
                           user=user)


@register_blueprint.route("/completed/<user_email>")
def completed(user_email):
    user = User.query.filter_by(email=user_email).one()
    if user.is_departmental_user():
        return render_template('register/completed_departmental.html', user=user)
    else:
        return render_template('register/completed_internal.html', user=user)

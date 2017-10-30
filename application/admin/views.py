from flask import render_template, url_for, redirect, current_app, flash, abort
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy.orm.exc import NoResultFound

from application import db, mail
from application.admin import admin_blueprint
from application.admin.forms import AddUserForm
from application.auth.models import User, Role
from application.utils import admin_required, generate_token


@admin_blueprint.route('/')
@admin_required
@login_required
def index():
    return render_template('admin/index.html')


@admin_blueprint.route('/users')
@admin_required
@login_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_blueprint.route('/users/<user_id>')
@admin_required
@login_required
def user(user_id):
    user = User.query.filter_by(id=user_id).one()
    has_all_roles = len(user.roles) == len(Role.query.all())
    return render_template('admin/user.html', user=user, has_all_roles=has_all_roles)


@admin_blueprint.route('/users/add', methods=('GET', 'POST'))
@admin_required
@login_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        role = Role.query.filter_by(name=form.user_type.data).one()
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        _send_account_activation_email(form.email.data, current_app)
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', form=form)

@admin_blueprint.route('/users/<user_id>/resend-account-activation-email')
@admin_required
@login_required
def resend_account_activation_email(user_id):
    try:
        user = User.query.get(user_id)
        _send_account_activation_email(user.email, current_app)
        return redirect(url_for('admin.users'))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(400)


@admin_blueprint.route('/users/<user_id>/deactivate')
@admin_required
@login_required
def deactivate_user(user_id):
    try:
        user = User.query.get(user_id)
        user.active = False
        db.session.add(user)
        db.session.commit()
        flash('User account for: %s deactivated' % user.email)
        return redirect(url_for('admin.users'))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)
    return render_template('admin/users.html', users=users)


@admin_blueprint.route('/site-build')
@admin_required
@login_required
def site_build():
    return render_template('admin/site_build.html')


def _send_account_activation_email(email, app):
    token = generate_token(email, app)
    confirmation_url = url_for('register.confirm_account',
                               token=token,
                               _external=True)
    html = render_template('admin/confirm_account.html', confirmation_url=confirmation_url, user=current_user)
    msg = Message(html=html,
                  subject="Access to the RDU CMS",
                  sender=app.config['RDU_EMAIL'],
                  recipients=[email])
    try:
        mail.send(msg)
        flash("User account invite sent to: %s." % email)
    except Exception as ex:
        flash("Failed to send invite to: %s" % email, 'error')
        app.logger.error(ex)

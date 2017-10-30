from flask import render_template, url_for, redirect, current_app, flash
from flask_login import login_required, current_user
from flask_mail import Message

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

        token = generate_token(form.email.data, current_app)
        confirmation_url = url_for('register.confirm_account',
                                   token=token,
                                   _external=True)

        html = render_template('admin/confirm_account.html', confirmation_url=confirmation_url, user=current_user)

        msg = Message(html=html,
                      subject="Access to the RDU CMS",
                      sender=current_app.config['RDU_EMAIL'],
                      recipients=[form.email.data])
        try:
            mail.send(msg)
            flash("User account invite sent to: %s." % form.email.data)
        except Exception as ex:
            flash("Failed to send invite to: %s" % form.email.data, 'error')
            current_app.logger.error(ex)

        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', form=form)


@admin_blueprint.route('/site-build')
@admin_required
@login_required
def site_build():
    return render_template('admin/site_build.html')

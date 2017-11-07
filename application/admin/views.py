from flask import render_template, url_for, redirect, current_app, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.admin import admin_blueprint
from application.admin.forms import AddUserForm
from application.auth.models import User, Role
from application.utils import admin_required, create_and_send_activation_email


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


@admin_blueprint.route('/users/<int:user_id>')
@admin_required
@login_required
def user_by_id(user_id):
    user = User.query.filter_by(id=user_id).one()
    has_all_roles = len(user.roles) == len(Role.query.all())
    return render_template('admin/user.html', user=user, has_all_roles=has_all_roles)


@admin_blueprint.route('/users/add', methods=('GET', 'POST'))
@admin_required
@login_required
def add_user():
    print('toot')
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        role = Role.query.filter_by(name=form.user_type.data).one()
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        create_and_send_activation_email(form.email.data, current_app)
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', form=form)


@admin_blueprint.route('/users/<int:user_id>/resend-account-activation-email')
@admin_required
@login_required
def resend_account_activation_email(user_id):
    try:
        user = User.query.get(user_id)
        create_and_send_activation_email(user.email, current_app)
        return redirect(url_for('admin.users'))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(400)


@admin_blueprint.route('/users/<int:user_id>/deactivate')
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


@admin_blueprint.route('/users/<int:user_id>/give-admin-rights')
@admin_required
@login_required
def give_user_admin_rights(user_id):
    try:
        user = User.query.get(user_id)
        if user.has_role('INTERNAL_USER'):
            admin_role = Role.query.filter_by(name='ADMIN').one()
            user.roles.append(admin_role)
            db.session.add(user)
            db.session.commit()
            flash('Gave admin rights to %s' % user.email)
        else:
            flash('Only internal users can be give admin rights')
        return redirect(url_for('admin.user_by_id', user_id=user.id))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)


@admin_blueprint.route('/users/<int:user_id>/remove-admin-rights')
@admin_required
@login_required
def remove_user_admin_rights(user_id):
    user = User.query.get(user_id)
    if user.id == current_user.id:
        flash("You can't remove your own admin rights")
    else:
        updated_roles = [r for r in user.roles if r.name != 'ADMIN']
        user.roles = updated_roles
        db.session.add(user)
        db.session.commit()
        flash('Removed admin rights from %s' % user.email)
    return redirect(url_for('admin.user_by_id', user_id=user.id))


@admin_blueprint.route('/site-build')
@admin_required
@login_required
def site_build():
    return render_template('admin/site_build.html')

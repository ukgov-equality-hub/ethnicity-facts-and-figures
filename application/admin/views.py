from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.admin import admin_blueprint
from application.admin.forms import AddUserForm
from application.auth.models import User, TypeOfUser, CAPABILITIES, MANAGE_SYSTEM, MANAGE_USERS
from application.cms.models import Page, user_page
from application.utils import create_and_send_activation_email, user_can


@admin_blueprint.route('/')
@user_can(MANAGE_USERS)
@login_required
def index():
    return render_template('admin/index.html')


@admin_blueprint.route('/users')
@user_can(MANAGE_USERS)
@login_required
def users():
    return render_template('admin/users.html', users=User.query.order_by(User.email).all())


@admin_blueprint.route('/users/<int:user_id>')
@user_can(MANAGE_USERS)
@login_required
def user_by_id(user_id):
    user = User.query.filter_by(id=user_id).one()
    if user.user_type == TypeOfUser.DEPT_USER:
        measures = db.session.query(Page.guid, Page.title)\
                                .filter(Page.page_type == 'measure')\
                                .order_by(Page.title).distinct().all()
        shared = Page.query.with_parent(user).distinct(Page.guid)
    else:
        measures = []
        shared = []

    return render_template('admin/user.html', user=user, measures=measures, shared=shared)


@admin_blueprint.route('/users/<int:user_id>/share', methods=['POST'])
@user_can(MANAGE_USERS)
@login_required
def share_page_with_user(user_id):
    page_id = request.form.get('measure-picker')
    page = Page.query.filter_by(guid=page_id).order_by(Page.created_at).first()
    user = User.query.get(user_id)
    if not user.is_departmental_user():
        flash('User %s is not a departmental user' % user.email, 'error')
    if user in page.shared_with:
        flash('User %s already has access to %s ' % (user.email, page.title), 'error')
    else:
        page.shared_with.append(user)
        db.session.add(page)
        db.session.commit()
    return redirect(url_for('admin.user_by_id', user_id=user_id, _anchor='departmental-sharing'))


@admin_blueprint.route('/users/<int:user_id>/remove-share/<page_id>')
@user_can(MANAGE_USERS)
@login_required
def remove_shared_page_from_user(user_id, page_id):
    db.session.execute(user_page.delete().where(user_page.c.user_id == user_id).where(user_page.c.page_id == page_id))
    db.session.commit()
    return redirect(url_for('admin.user_by_id', user_id=user_id, _anchor='departmental-sharing'))


@admin_blueprint.route('/users/add', methods=('GET', 'POST'))
@user_can(MANAGE_USERS)
@login_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():

        existing_user = User.query.filter(User.email.ilike(form.email.data)).first()
        if existing_user:
            message = 'User: %s is already in the system' % existing_user.email
            flash(message, 'error')
            return redirect(url_for('admin.users'))

        user = User(email=form.email.data)
        if form.user_type.data == TypeOfUser.DEPT_USER.name:
            user.user_type = TypeOfUser.DEPT_USER
            user.capabilities = CAPABILITIES[TypeOfUser.DEPT_USER]
        elif form.user_type.data == TypeOfUser.RDU_USER.name:
            user.user_type = TypeOfUser.RDU_USER
            user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
        elif form.user_type.data == TypeOfUser.DEV_USER.name:
            user.user_type = TypeOfUser.DEV_USER
            user.capabilities = CAPABILITIES[TypeOfUser.DEV_USER]
        else:
            flash('Only RDU or DEPT users can be created using this page')
            abort(401)

        db.session.add(user)
        db.session.commit()
        create_and_send_activation_email(form.email.data, current_app)
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', form=form)


@admin_blueprint.route('/users/<int:user_id>/resend-account-activation-email')
@user_can(MANAGE_USERS)
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
@user_can(MANAGE_USERS)
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


@admin_blueprint.route('/users/<int:user_id>/delete')
@user_can(MANAGE_USERS)
@login_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        for page in user.pages:
            db.session.execute(user_page.delete()
                               .where(user_page.c.user_id == user.id)
                               .where(user_page.c.page_id == page.guid))
            db.session.commit()
        db.session.delete(user)
        db.session.commit()
        flash('User account for: %s deleted' % user.email)
        return redirect(url_for('admin.users'))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)
    return render_template('admin/users.html', users=users)


@admin_blueprint.route('/users/<int:user_id>/make-admin')
@user_can(MANAGE_USERS)
@login_required
def make_admin_user(user_id):
    try:
        user = User.query.get(user_id)
        if user.is_rdu_user():
            user.user_type = TypeOfUser.ADMIN_USER
            user.capabilities = CAPABILITIES[TypeOfUser.ADMIN_USER]
            db.session.add(user)
            db.session.commit()
            flash('User %s is now an admin user' % user.email)
        else:
            flash('Only RDU users can be made admin')
        return redirect(url_for('admin.user_by_id', user_id=user.id))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)


@admin_blueprint.route('/users/<int:user_id>/make-rdu-user')
@user_can(MANAGE_USERS)
@login_required
def make_rdu_user(user_id):
    user = User.query.get(user_id)
    if user.id == current_user.id:
        flash("You can't remove your own admin rights")
    elif user.user_type == TypeOfUser.ADMIN_USER:
        user.user_type = TypeOfUser.RDU_USER
        user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
        db.session.add(user)
        db.session.commit()
        flash('User %s is now a standard RDU user' % user.email)
    else:
        flash("Only admins can be changed to standard RDU user")
    return redirect(url_for('admin.user_by_id', user_id=user.id))


@admin_blueprint.route('/site-build')
@user_can(MANAGE_SYSTEM)
@login_required
def site_build():
    return render_template('admin/site_build.html')

from flask_security import (
    UserMixin,
    RoleMixin
)

from flask_principal import Permission, RoleNeed
from sqlalchemy import DateTime

from application import db

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return '%s - %s' % (self.name, self.description)


class User(db.Model, UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())

    # TODO remove distinction between internal and departmental user. Instead have users and admin users
    # to restrict views to specific measures, instead we can have notion of ownership of page, i.e. page created
    # by and then that user can share page with specific user or all users.

    def is_departmental_user(self):
        permissions = [Permission(RoleNeed('DEPARTMENTAL_USER')) for role in self.roles]
        for p in permissions:
            if p.can():
                return True
        else:
            return False

    def is_internal_user(self):
        permissions = [Permission(RoleNeed('INTERNAL_USER')) or Permission(RoleNeed('ADMIN')) for role in self.roles]
        for p in permissions:
            if p.can():
                return True
        else:
            return False

    def is_admin(self):
        permissions = [Permission(RoleNeed('ADMIN')) for role in self.roles]
        for p in permissions:
            if p.can():
                return True
        else:
            return False

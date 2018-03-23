from flask_security import UserMixin, RoleMixin
from sqlalchemy.dialects.postgresql import ARRAY
from application import db
from sqlalchemy.ext.mutable import MutableList

INTERNAL_USER = 'INTERNAL_USER'
DEPARTMENTAL_USER = 'DEPARTMENTAL_USER'
ADMIN = 'ADMIN'


class RoleFreeUserMixin(UserMixin):

    def has_role(self, role):
        return role in self.capabilities


class User(db.Model, RoleFreeUserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    capabilities = db.Column(MutableList.as_mutable(ARRAY(db.String)), default=[])

    def user_name(self):
        return self.email.split('@')[0]

    def is_departmental_user(self):
        return 'DEPARTMENTAL_USER' in self.capabilities

    def is_internal_user(self):
        return 'INTERNAL_USER' in self.capabilities

    def is_admin(self):
        return 'ADMIN' in self.capabilities

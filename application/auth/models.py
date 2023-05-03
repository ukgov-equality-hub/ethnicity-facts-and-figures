import enum

from flask_security import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from application import db
from sqlalchemy.ext.mutable import MutableList


class TypeOfUser(enum.Enum):
    RDU_USER = "RDU user"
    DEPT_USER = "Departmental user"
    ADMIN_USER = "RDU admin"
    DEV_USER = "RDU developer"


COPY_MEASURE = "copy_measure"
CREATE_MEASURE = "create_measure"
CREATE_VERSION = "create_version"
DELETE_MEASURE = "delete_measure"
MANAGE_SYSTEM = "manage_system"
MANAGE_USERS = "manage_users"
MANAGE_DATA_SOURCES = "manage_data_sources"
ORDER_MEASURES = "order_measures"
PUBLISH = "publish"
READ = "read"
UPDATE_MEASURE = "update_measure"
VIEW_DASHBOARDS = "view_dashboards"
MANAGE_TOPICS = "manage_topics"

DEPT = [READ, UPDATE_MEASURE, CREATE_VERSION]
RDU = DEPT + [CREATE_MEASURE, DELETE_MEASURE, VIEW_DASHBOARDS]
ADMIN = RDU + [PUBLISH, MANAGE_USERS, ORDER_MEASURES, MANAGE_DATA_SOURCES, MANAGE_TOPICS, MANAGE_SYSTEM]
DEV = ADMIN + [COPY_MEASURE, MANAGE_DATA_SOURCES]

CAPABILITIES = {
    TypeOfUser.DEPT_USER: DEPT,
    TypeOfUser.RDU_USER: RDU,
    TypeOfUser.ADMIN_USER: ADMIN,
    TypeOfUser.DEV_USER: DEV,
}


class RoleFreeUserMixin(UserMixin):
    def has_role(self, role):
        return role in self.capabilities


class User(db.Model, RoleFreeUserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean(), default=False)
    confirmed_at = db.Column(db.DateTime())
    user_type = db.Column(db.Enum(TypeOfUser, name="type_of_user_types"), nullable=False)
    capabilities = db.Column(MutableList.as_mutable(ARRAY(db.String)), default=[])
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(16))
    current_login_ip = db.Column(db.String(16))
    login_count = db.Column(db.Integer)
    failed_login_count = db.Column(db.Integer, default=0)

    # relationships
    measures = db.relationship(
        "Measure",
        lazy="subquery",
        secondary="user_measure",
        primaryjoin="User.id == user_measure.columns.user_id",
        secondaryjoin="Measure.id == user_measure.columns.measure_id",
        back_populates="shared_with",
    )

    __table_args__ = (UniqueConstraint(email, name="uq_users_email"),)

    def user_name(self):
        if '@' in self.email:
            return self.email.split("@")[0]
        return self.email

    def is_departmental_user(self):
        return self.user_type == TypeOfUser.DEPT_USER

    def is_rdu_user(self):
        return self.user_type == TypeOfUser.RDU_USER

    def is_admin_user(self):
        return self.user_type == TypeOfUser.ADMIN_USER

    def can(self, capability):
        return capability in self.capabilities

    def can_access_measure(self, measure):
        if self.user_type != TypeOfUser.DEPT_USER:
            return True
        else:
            return self in measure.shared_with

    # DEPRECATED: use `can_access_measure` method instead.
    def can_access(self, measure_slug):
        if self.user_type != TypeOfUser.DEPT_USER:
            return True
        else:
            if any(measure.slug == measure_slug for measure in self.measures):
                return True
            else:
                return False


class UserAttemptedToLogin(db.Model, RoleFreeUserMixin):
    __tablename__ = "invalid_user_login_attempt"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    ip = db.Column(db.String(16))
    failed_login_count = db.Column(db.Integer, default=0)

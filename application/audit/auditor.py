import sqreen

from application.audit.models import Audit
from application import db


def record_login(sender, **kwargs):
    sqreen.auth_track(True, username=kwargs['user'].email)


def record_logout(sender, **kwargs):
    _log_it(kwargs['user'], 'logout')


def _log_it(user, action):
    audit = Audit(user=user.email, action=action)
    db.session.add(audit)
    db.session.commit()

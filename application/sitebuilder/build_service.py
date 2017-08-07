import uuid
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

from application.sitebuilder.models import Build
from application import db
from application.sitebuilder.build import do_it


def request_build():
    build = Build()
    build.id = str(uuid.uuid4())
    db.session.add(build)
    db.session.commit()


def build_site(app):
    Session = sessionmaker(db.engine)
    with make_session_scope(Session) as session:
        builds = session.query(Build).filter(Build.status == 'PENDING').order_by(desc(Build.created_at)).all()
        if not builds:
            print('No pending builds at', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            return
        superseded = []
        for i, build in enumerate(builds):
            if build.status == 'PENDING':
                _start_build(app, build, session)
                superseded.extend(builds[i+1:])
                break
        for b in superseded:
            _mark_build_superseded(b, session)


def _start_build(app, build, session):
    try:
        _mark_build_started(build, session)
        do_it(app, build)
        build.status = 'DONE'
        build.succeeded_at = datetime.utcnow()
        session.add(build)
    except Exception as e:
        build.status = 'FAILED'
        build.failed_at = datetime.utcnow()
        build.failure_reason = str(e)
    finally:
        session.add(build)


def _mark_build_started(build, session):
    build.status = 'STARTED'
    session.add(build)
    session.commit()


def _mark_build_superseded(build, session):
    if build.status == 'PENDING':
        build.status = 'SUPERSEDED'
        session.add(build)


@contextmanager
def make_session_scope(Session):
    session = Session()
    session.expire_on_commit = False
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

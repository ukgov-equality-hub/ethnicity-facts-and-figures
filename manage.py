#! /usr/bin/env python
import os

import sys
from flask_script import Manager, Server
from flask_security import SQLAlchemyUserDatastore

from flask_migrate import (
    Migrate,
    MigrateCommand
)

from sqlalchemy import desc, func

from application.admin.forms import is_gov_email
from application.cms.categorisation_service import categorisation_service
from application.cms.exceptions import CategorisationNotFoundException
from application.factory import create_app
from application.config import Config, DevConfig
from application.auth.models import *
from application.cms.models import *
from application.sitebuilder.models import *
from application.utils import create_and_send_activation_email, send_email

env = os.environ.get('ENVIRONMENT', 'DEV')
# if env.lower() == 'dev':
#     app = create_app(DevConfig)
# else:
#     app = create_app(Config)
app = create_app(DevConfig)

manager = Manager(app)
manager.add_command("server", Server())

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


# Note not using Flask-Security Role model
user_datastore = SQLAlchemyUserDatastore(db, User, None)


@manager.option('--email', dest='email')
def create_local_user_account(email):
    if is_gov_email(email):
        user = user_datastore.find_user(email=email)
        if user:
            print("User %s already exists" % email)
        else:
            user = User(email=email)
            user.capabilities = [INTERNAL_USER]
            db.session.add(user)
            db.session.commit()
            confirmation_url = create_and_send_activation_email(email, app, devmode=True)
            print('User account created. To complete process go to %s' % confirmation_url)
    else:
        print('email is not a gov.uk email address and has not been whitelisted')


@manager.option('--email', dest='email')
def add_admin_role_to_user(email):
    user = user_datastore.find_user(email=email)
    if user.is_departmental_user():
        print("You can't give admin rights to a deparmtent user")
    elif user.is_admin():
        print("User already has admin rights")
    else:
        user.capabilities.append(ADMIN)
        db.session.add(user)
        db.session.commit()
        print('User given admin rights')


@manager.option('--code', dest='code')
def delete_categorisation(code):

    try:
        category = categorisation_service.get_categorisation_by_code(code)
        if category.dimension_links.count() > 0:
            print('Error: Category %s is still linked to dimensions and cannot be deleted' % code)
        else:
            categorisation_service.delete_categorisation(category)
    except CategorisationNotFoundException as e:
        print('Error: Could not find category with code %s' % code)


@manager.command
def sync_categorisations():
    categorisation_service.synchronise_categorisations_from_file('./application/data/ethnicity_categories.csv')
    categorisation_service.synchronise_values_from_file('./application/data/ethnicity_categorisation_values.csv')


@manager.command
def import_dimension_categorisations():
    # import current categorisations before doing the dimension import
    categorisation_service.synchronise_categorisations_from_file('./application/data/ethnicity_categories.csv')

    file = './application/data/imports/dimension_categorisation_import2.csv'
    categorisation_service.import_dimension_categorisations_from_file(file_name=file)


@manager.command
def build_static_site():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import build_site
        build_site(app)
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.command
def request_static_build():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import request_build
        request_build()
        print('A build has been requested. It could be up to ten minutes before the request is processed')
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.command
def force_build_static_site():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import request_build
        from application.sitebuilder.build_service import build_site
        request_build()
        build_site(app)
        print('An immediate build has been requested')
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.command
def pull_from_prod_database():
    environment = os.environ.get('ENVIRONMENT', 'PRODUCTION')
    if environment == 'PRODUCTION':
        print('It looks like you are running this in production or some unknown environment.')
        print('Do not run this command in this environment as it deletes data')
        sys.exit(-1)

    prod_db = os.environ.get('PROD_DB_URL')
    if prod_db is None:
        print("You need to set an environment variable 'PROD_DB_URL' with value of production postgres url")
        sys.exit(-1)

    import subprocess
    import shlex
    out_file = '/tmp/data.dump'
    command = 'scripts/get_data.sh %s %s' % (prod_db, out_file)
    subprocess.call(shlex.split(command))

    db.session.execute('DELETE FROM association;')
    db.session.execute('DELETE FROM parent_association;')
    db.session.execute('DELETE FROM categorisation_value;')
    db.session.execute('DELETE FROM dimension_categorisation;')
    db.session.execute('DELETE FROM categorisation;')
    db.session.execute('DELETE FROM dimension;')
    db.session.execute('DELETE FROM upload;')
    db.session.execute('DELETE FROM page;')
    db.session.execute('DELETE FROM frequency_of_release;')
    db.session.execute('DELETE FROM lowest_level_of_geography;')
    db.session.execute('DELETE FROM organisation;')
    db.session.execute('DELETE FROM type_of_statistic;')
    db.session.commit()

    command = 'pg_restore -d %s %s' % (app.config['SQLALCHEMY_DATABASE_URI'], out_file)
    subprocess.call(shlex.split(command))

    import contextlib
    with contextlib.suppress(FileNotFoundError):
        os.remove(out_file)

    print('Loaded data to', app.config['SQLALCHEMY_DATABASE_URI'])


@manager.command
def delete_old_builds():
    from datetime import date
    a_week_ago = date.today() - timedelta(days=7)
    out = db.session.query(Build).filter(Build.created_at < a_week_ago).delete()
    db.session.commit()
    print('Deleted %d old builds' % out)


@manager.command
def report_broken_build():
    from datetime import date
    yesterday = date.today() - timedelta(days=1)
    failed = db.session.query(Build).filter(Build.status == 'FAILED',
                                            Build.created_at > yesterday).order_by(desc(Build.created_at)).first()
    if failed:
        message = 'Build failure in application %s. Build id %s created at %s' % (app.config['ENVIRONMENT'],
                                                                                  failed.id,
                                                                                  failed.created_at)
        subject = "Build failure in application %s on %s" % (app.config['ENVIRONMENT'], date.today())
        recipients = db.session.query(User).filter(User.capabilities.any('DEVELOPER')).all()
        for r in recipients:
            send_email(app.config['RDU_EMAIL'], r.email, message, subject)
        print(message)
    else:
        print('No failed builds today')


@manager.command
def report_stalled_build():
    from datetime import date
    half_an_hour_ago = datetime.now() - timedelta(minutes=30)
    stalled = db.session.query(Build).filter(Build.status == 'STARTED',
                                             func.DATE(Build.created_at) == date.today(),
                                             Build.created_at <= half_an_hour_ago).order_by(
        desc(Build.created_at)).first()

    if stalled:
        message = 'Build stalled for more than 30 minutes in application %s. Build id %s created at %s' % (
            app.config['ENVIRONMENT'],
            stalled.id,
            stalled.created_at)
        subject = "Build stalled in application %s on %s" % (app.config['ENVIRONMENT'], date.today())
        recipients = db.session.query(User).filter(User.capabilities.any('DEVELOPER')).all()
        for r in recipients:
            send_email(app.config['RDU_EMAIL'], r.email, message, subject)
        print(message)
    else:
        print('No stalled builds')


@manager.command
def refresh_materialized_views():

    db.session.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY latest_published_pages;')
    db.session.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY pages_by_geography;')
    db.session.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY ethnic_groups_by_dimension;')
    db.session.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY categorisations_by_dimension;')
    db.session.commit()

    print('Refreshed data for MATERIALIZED VIEWS')


# Build stalled or failed emails continue until status is updated using
# this command.
@manager.option('--build_id', dest='build_id')
def acknowledge_build_issue(build_id):
    try:
        build = db.session.query(Build).filter(Build.id == build_id).one()
        build.status = 'SUPERSEDED'
        db.session.add(build)
        db.session.commit()
        print('Build id', build_id, 'set to superseded')
    except sqlalchemy.orm.exc.NoResultFound:
        print('No build found with id', build_id)


if __name__ == '__main__':
    manager.run()

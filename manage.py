#! /usr/bin/env python
import os
import json
import shutil

import sys
from flask_script import Manager, Server

from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password

from flask_migrate import (
    Migrate,
    MigrateCommand
)
from slugify import slugify

from application.cms.page_service import page_service
from application.factory import create_app
from application.config import Config, DevConfig
from application.auth.models import *
from application.cms.models import *
from application.sitebuilder.models import *

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

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@manager.option('--email', dest='email')
def add_admin_role_to_user(email):
    user = user_datastore.find_user(email=email)
    if user.has_role('DEPARTMENTAL_USER'):
        print("You can't give admin rights to a deparmtent user")
    elif user.has_role('ADMIN'):
        print("User already has admin rights")
    else:
        role = Role.query.filter_by(name='ADMIN').first()
        user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        print('User given admin rights')


@manager.command
def create_roles():
    for role in [('ADMIN', 'Application administrator'),
                 ('INTERNAL_USER', 'A user in the RDU team who can add, edit and view all pages'),
                 ('DEPARTMENTAL_USER', 'A user that can view pages that have a status of departmental review'),
                 ]:
        role = user_datastore.create_role(name=role[0], description=role[1])
        db.session.add(role)
        db.session.commit()


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


if __name__ == '__main__':
    manager.run()

#! /usr/bin/env python
import os
import json
from flask_script import Manager, Server

from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password

from flask_migrate import (
    Migrate,
    MigrateCommand
)

from application.factory import create_app
from application.config import Config, DevConfig
from application.auth.models import *
from application.cms.models import *
from application.sitebuilder.models import *

env = os.environ.get('ENVIRONMENT', 'DEV')
if env == 'DEV':
    app = create_app(DevConfig)
else:
    app = create_app(Config)

manager = Manager(app)
manager.add_command("server", Server())

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@manager.option('--email', dest='email')
@manager.option('--password', dest='password')
def create_internal_user(email, password):
    if not user_datastore.find_user(email=email):
        user = user_datastore.create_user(
            email=email,
            password=encrypt_password(password),
            roles=['INTERNAL_USER'])
        db.session.add(user)
        db.session.commit()
        return user


@manager.option('--email', dest='email')
@manager.option('--password', dest='password')
def create_departmental_user(email, password):
    if not user_datastore.find_user(email=email):
        user = user_datastore.create_user(
            email=email,
            password=encrypt_password(password),
            roles=['DEPARTMENTAL_USER'])
        db.session.add(user)
        db.session.commit()
        return user


@manager.option('--email', dest='email')
@manager.option('--role', dest='role')
def add_role_to_user(email, role):
    user = user_datastore.find_user(email=email)
    role = Role.query.filter_by(name=role.upper()).first()
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()


@manager.command
def create_roles():
    for role in [('ADMIN', 'Application administrator'),
                 ('INTERNAL_USER', 'A user in the RDU team who can add, edit and view all pages'),
                 ('DEPARTMENTAL_USER', 'A user that can view pages that have a status of departmental review'),
                 ]:
        role = user_datastore.create_role(name=role[0], description=role[1])
        db.session.add(role)
        db.session.commit()


@manager.option('--email', dest='email')
@manager.option('--newpass', dest='new_password')
def update_password(email, new_password):
    user = user_datastore.find_user(email=email)
    if user is not None:
        user.password = encrypt_password(new_password.strip())
        db.session.add(user)
        db.session.commit()
        print('password updated')
    else:
        print('Could not find user with email %s', email)


def set_dimension_source_data(page_dict, root):
    for d in page_dict.get('dimensions', []):
        source_dir = os.path.join(root, 'source', d['guid'])
        chart_source = os.path.join(source_dir, 'chart.json')
        if os.path.isfile(chart_source):
            with open(chart_source) as chart_source_file:
                chart_source_data = json.load(chart_source_file)
                d['chart_source_data'] = chart_source_data

        table_source = os.path.join(source_dir, 'table.json')
        if os.path.isfile(table_source):
            with open(table_source) as table_source_file:
                table_source_data = json.load(table_source_file)
                d['table_source_data'] = table_source_data


@manager.command
def build_static_site():
    from application.sitebuilder.build_service import build_site
    build_site(app)


@manager.command
def force_build_static_site():
    from application.sitebuilder.build_service import build_site
    from application.sitebuilder.build_service import initiate_build
    initiate_build()
    build_site(app)


if __name__ == '__main__':
    manager.run()

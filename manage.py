#! /usr/bin/env python

from flask_script import Manager, Server

from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password

from flask_migrate import (
    Migrate,
    MigrateCommand
)

from application.factory import create_app
from application.config import DevConfig
from application.auth.models import *
from application.cms.models import DbPage


app = create_app(DevConfig)

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


@manager.option('--path', dest='path')
def load_data(path):
    loaded = {'homepage': 0, 'topic': 0, 'subtopic': 0, 'measure': 0}
    import os
    import json
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == 'meta.json':
                meta_path = os.path.join(root, file)
                page_path = os.path.join(root, 'page.json')

                with open(meta_path) as meta_file:
                    meta_json = json.load(meta_file)

                with open(page_path) as page_file:
                    page_json = page_file.read()

                page_dict = json.loads(page_json)
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

                db_page = DbPage(guid=meta_json['guid'],
                                 uri=meta_json['uri'],
                                 parent_guid=meta_json['parent'] if meta_json['parent'] else None,
                                 page_type=meta_json['type'],
                                 status=meta_json['status'])

                db_page.page_json = json.dumps(page_dict)
                db.session.add(db_page)
                db.session.commit()

                loaded[meta_json['type']] = loaded[meta_json['type']] + 1

    print("Loaded", loaded)


if __name__ == '__main__':
    manager.run()

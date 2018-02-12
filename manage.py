#! /usr/bin/env python
import os

from flask_script import Manager, Server
from flask_security import SQLAlchemyUserDatastore

from flask_migrate import (
    Migrate,
    MigrateCommand
)

from application.admin.forms import is_gov_email
from application.cms.category_service import category_service
from application.factory import create_app
from application.config import Config, DevConfig
from application.auth.models import *
from application.cms.models import *
from application.sitebuilder.models import *
from application.utils import create_and_send_activation_email

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
def create_local_user_account(email):
    if is_gov_email(email):
        user = user_datastore.find_user(email=email)
        if user:
            print("User %s already exists" % email)
        else:
            user = User(email=email)
            role = Role.query.filter_by(name='INTERNAL_USER').first()
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            confirmation_url = create_and_send_activation_email(email, app, devmode=True)
            print('User account created. To complete process go to %s' % confirmation_url)
    else:
        print('email is not a gov.uk email address and has not been whitelisted')


@manager.option('--email', dest='email')
def create_user_account(email):
    if is_gov_email(email):
        user = user_datastore.find_user(email=email)
        if user:
            print("User %s already exists" % email)
        else:
            user = User(email=email)
            role = Role.query.filter_by(name='INTERNAL_USER').first()
            user.roles.append(role)
            db.session.add(user)
            db.session.commit()
            create_and_send_activation_email(email, app)
            print('User account created and activation email sent to %s' % email)
    else:
        print('email is not a gov.uk email address and has not been whitelisted')


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
def create_ethnicity_categories():
    data = [['Common', 'White and Other', 1, ['White', 'Other']],
            ['Common', 'White British and Other', 2, ['White British', 'Other']],
            ['Common', 'ONS 2011 5+1', 3, ['Asian', 'Black', 'Mixed', 'White', 'Other']],
            ['Common', 'ONS 2011 18+1', 4, ['Bangladeshi', 'Indian', 'Chinese', 'Pakistani', 'Asian other',
                                            'Black African', 'Black Caribbean', 'Black other',
                                            'Mixed White/Black African', 'Mixed White/Black African',
                                            'Mixed White/Asian', 'Mixed other',
                                            'White British', 'White Irish', 'White other', 'Gypsy or Irish Traveller',
                                            'Arab', 'Any other ethnic group']],
            ['Common', 'ONS 2001 5+1', 5, ['Asian', 'Black', 'Mixed', 'White', 'Chinese and Other']],
            ['Common', 'ONS 2001 16+1', 6, ['Bangladeshi', 'Indian', 'Pakistani', 'Asian other',
                                            'Black African', 'Black Caribbean', 'Black other',
                                            'Mixed White/Black African', 'Mixed White/Black African',
                                            'Mixed White/Asian', 'Mixed other',
                                            'White British', 'White Irish', 'White other',
                                            'Chinese', 'Any other ethnic group']],
            ['Other', 'ONS 2011 5+1 (Mixed included in Other)', 1, ['Asian', 'Black', 'White', 'Other']],
            ['Other', 'ONS 2011 5+1 (Asian included in Other)', 2, ['Black', 'Mixed', 'White', 'Other']],
            ['Other', 'ONS 2011 5+1 (plus Chinese)', 3, ['Asian', 'Chinese', 'Black', 'Mixed', 'White', 'Other']],
            ['Other', 'ONS 2011 5+1 (Asian expanded)', 4,
             ['Bangladeshi', 'Indian', 'Chinese', 'Pakistani', 'Asian other', 'Black', 'Mixed', 'White', 'Other']],
            ['Other', 'ONS 2011 5+1 (Asian expanded, Mixed included in Other)', 5,
             ['Bangladeshi', 'Indian', 'Chinese', 'Pakistani', 'Asian other', 'Black', 'White', 'Other']],
            ['Other', 'ONS 2001 16+1 (plus Irish Traveller, plus Gypsy/Roma)', 6,
             ['Bangladeshi', 'Indian', 'Pakistani', 'Asian other',
              'Black African', 'Black Caribbean', 'Black other',
              'Mixed White/Black African', 'Mixed White/Black African',
              'Mixed White/Asian', 'Mixed other',
              'White British', 'White Irish', 'White other',
              'Irish Traveller', 'Gypsy/Roma',
              'Chinese', 'Any other ethnic group']]
            ]
    for category in data:
        category_service.create_category(family='Ethnicity',
                                         subfamily=category[0],
                                         title=category[1],
                                         position=category[2])
        category_service.add_category_values_to_category('Ethnicity', category[1], category[3])


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

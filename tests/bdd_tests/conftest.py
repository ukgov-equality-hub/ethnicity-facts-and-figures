import json
import os
import tempfile
import pytest
import datetime

from slugify import slugify
from application.cms.models import DbPage
from application.auth.models import User, Role
from application.cms.page_service import PageService
from application.config import TestConfig
from application.factory import create_app


@pytest.fixture(scope='module')
def bdd_empty_app(request):
    _app = create_app(TestConfig)

    ctx = _app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return _app


@pytest.fixture(scope='module')
def bdd_app(bdd_empty_app, bdd_db):

    PageService().create_page('homepage', None, data={
        'title': 'homepage',
        'guid': 'homepage',
        'publication_date': datetime.date.today()

    })
    PageService().create_page('topic', 'homepage', data={
        'title': 'Bdd Topic Page',
        'guid': 'bdd_topic',
        'publication_date': datetime.date.today()

    })
    PageService().create_page('subtopic', 'bdd_topic', data={
        'title': 'Bdd Subtopic Page',
        'guid': 'bdd_subtopic',
        'publication_date': datetime.date.today()

    })

    return bdd_empty_app


@pytest.fixture(scope='function')
def bdd_app_client(bdd_app):
    return bdd_app.test_client()


@pytest.fixture(scope='module')
def bdd_app_editor(bdd_db_session, bdd_internal_role):
    user = User(email='editor@methods.co.uk', password='password123')
    user.roles = [bdd_internal_role]
    bdd_db_session.session.add(user)
    bdd_db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def bdd_internal_role(bdd_db_session):
    role = Role(name='INTERNAL_USER', description='An internal user')
    bdd_db_session.session.add(role)
    bdd_db_session.session.commit()
    return role


@pytest.fixture(scope='module')
def bdd_app_reviewer(bdd_db_session, bdd_internal_role):
    user = User(email='reviewer@methods.co.uk', password='password123')
    user.roles = [bdd_internal_role]
    bdd_db_session.session.add(user)
    bdd_db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def bdd_departmental_role(bdd_db_session):
    role = Role(name='DEPARTMENTAL_USER', description='A departmental user')
    bdd_db_session.session.add(role)
    bdd_db_session.session.commit()
    return role


@pytest.fixture(scope='module')
def bdd_app_department(bdd_db_session, bdd_departmental_role):
    user = User(email='department@methods.co.uk', password='password123')
    user.roles = [bdd_departmental_role]
    bdd_db_session.session.add(user)
    bdd_db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def bdd_db(bdd_empty_app):
    from flask_migrate import Migrate, MigrateCommand
    from flask_script import Manager
    from alembic.command import upgrade
    from alembic.config import Config

    from application import db

    # TODO: Improve this
    test_dbs = ['postgresql://localhost/rdcms_test',
                'postgres://ubuntu:ubuntu@127.0.0.1:5433/circle_test',
                'postgresql://postgres@localhost:5439/rdcms_test',
                'postgres://ubuntu:ubuntu@127.0.0.1:5433/circle_test']

    assert str(db.engine.url) in test_dbs, 'only run tests against test db'

    Migrate(bdd_empty_app, db)
    Manager(db, MigrateCommand)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ALEMBIC_CONFIG = os.path.join(BASE_DIR, 'migrations')
    config = Config(ALEMBIC_CONFIG + '/alembic.ini')
    config.set_main_option("script_location", ALEMBIC_CONFIG)

    with bdd_empty_app.app_context():
        upgrade(config, 'head')

    yield db

    db.session.remove()
    db.get_engine(bdd_empty_app).dispose()


@pytest.fixture(scope='module')
def bdd_db_session(bdd_db):
    yield bdd_db

    bdd_db.session.remove()

    # this deletes any data in tables, but if you want to start from scratch (i.e. migrations etc, drop everything)
    # delete roles_users first
    roles_users = bdd_db.metadata.tables['roles_users']
    bdd_db.engine.execute(roles_users.delete())
    for tbl in bdd_db.metadata.sorted_tables:
        bdd_db.engine.execute(tbl.delete())

        bdd_db.session.commit()


@pytest.fixture(scope='function')
def stub_topic_page(bdd_db_session):

    page = DbPage(guid='bdd_topic',
                  parent_guid=None,
                  page_type='topic',
                  uri='test-topic-page',
                  status='DRAFT')

    page.page_json = json.dumps({'title': 'Test topic page'})

    bdd_db_session.session.add(page)
    bdd_db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_subtopic_page(bdd_db_session, stub_topic_page):

    page = DbPage(guid='bdd_subtopic',
                  parent_guid=stub_topic_page.guid,
                  page_type='subtopic',
                  uri='test-subtopic-page',
                  status='DRAFT')

    page.page_json = json.dumps({'title': 'Test subtopic page'})

    bdd_db_session.session.add(page)
    bdd_db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_page(bdd_db_session, stub_subtopic_page, stub_measure_form_data):

    page = DbPage(guid='bdd_measure',
                  parent_guid=stub_subtopic_page.guid,
                  page_type='measure',
                  uri='test-measure-page',
                  status='DRAFT')

    page.page_json = json.dumps(stub_measure_form_data)

    bdd_db_session.session.add(page)
    bdd_db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_form_data():
    return {'title': "Test Measure Page",
            'short_title': "Measure Page",
            'measure_summary': "Unemployment summary",
            'estimation': "X people are unemployed",
            'type_of_statistic': "type of statistic",
            'data_source_purpose': 'data_source_purpose',
            'qmi_text': "Quality and Methodology Information",
            'need_to_know': "Need to know this",
            'contact_name': "Jane Doe",
            'contact_email': "janedoe@example.com",
            'contact_phone': '',
            'summary': "Unemployment Sum",
            'data_type': "statistics",
            'frequency': "Quarterly",
            'ethnicity_definition_summary': "Ethnicity information",
            'qmi_url': "http://example.com",
            'guid': "test-measure-page",
            'time_covered': "4 months",
            'geographic_coverage': "United Kingdom",
            'department_source': "DWP",
            'ethnicity_definition_detail': "Detailed ethnicity information",
            'methodology': "how we measure unemployment",
            'published_date': "15th May 2017",
            'next_update_date': 'Ad hoc',
            'quality_assurance': "Quality assurance",
            'last_update_date': "15th May 2017",
            'revisions': '',
            'source_text': "DWP Stats",
            'source_url': "http://example.com",
            'disclosure_control': "disclosure",
            'further_technical_information': 'further_technical_information',
            'suppression_rules': "suppression rules",
            'related_publications': "related publications",
            'lowest_level_of_geography': "lowest_level_of_geography",
            'publication_date': datetime.now().date().strftime('Y%-%m-%d')
            }

import json
import os
import pytest
import datetime

from application.cms.category_service import CategoryService
from application.cms.models import *
from application.auth.models import *

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
def bdd_app(bdd_empty_app, bdd_db, bdd_app_editor):
    page_service = PageService()
    page_service.init_app(bdd_empty_app)

    category_service = CategoryService()
    category_service.init_app(bdd_empty_app)

    category = category_service.create_category('Ethnicity', 'Test', 'ONS 5+1', 1)
    category_service.add_category_value_to_category('Ethnicity', 'ONS 5+1', 'Asian')
    category_service.add_category_value_to_category('Ethnicity', 'ONS 5+1', 'Black')
    category_service.add_category_value_to_category('Ethnicity', 'ONS 5+1', 'Mixed')
    category_service.add_category_value_to_category('Ethnicity', 'ONS 5+1', 'White')
    category_service.add_category_value_to_category('Ethnicity', 'ONS 5+1', 'Other')

    homepage = page_service.create_page('homepage', None, data={
        'title': 'homepage',
        'guid': 'homepage',
        'publication_date': datetime.now().date()

    }, created_by=bdd_app_editor.email)
    bdd_topic_page = page_service.create_page('topic', homepage, data={
        'title': 'Bdd Topic Page',
        'guid': 'bdd_topic',
        'publication_date': datetime.now().date()

    }, created_by=bdd_app_editor.email)
    page_service.create_page('subtopic', bdd_topic_page, data={
        'title': 'Bdd Subtopic Page',
        'guid': 'bdd_subtopic',
        'publication_date': datetime.now().date()

    }, created_by=bdd_app_editor.email)

    bdd_db.engine.execute('''
        INSERT INTO frequency_of_release (id, position, description) VALUES (1, 1, 'Quarterly');
        INSERT INTO type_of_statistic (id, internal, external, position)
        VALUES (1, 'National Statistics (certified against a Code of Practice)', 'National Statistics', 1);
        INSERT INTO lowest_level_of_geography (name, position) VALUES ('UK', 0);
        INSERT INTO organisation (id, name, organisation_type, abbreviations, other_names)
        VALUES ('D10', 'Department for Work and Pensions', 'MINISTERIAL_DEPARTMENT', '{}', '{}');
        ''')

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
    user = User(email='reviewer@methods.co.uk', password='password123', active=True)
    user.roles = [bdd_internal_role]
    bdd_db_session.session.add(user)
    bdd_db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def bdd_departmental_role(bdd_db_session):
    role = Role(name='DEPARTMENTAL_USER', description='A departmental user', active=True)
    bdd_db_session.session.add(role)
    bdd_db_session.session.commit()
    return role


@pytest.fixture(scope='module')
def bdd_app_department(bdd_db_session, bdd_departmental_role):
    user = User(email='department@methods.co.uk', password='password123', active=True)
    user.roles = [bdd_departmental_role]
    bdd_db_session.session.add(user)
    bdd_db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def bdd_db(bdd_empty_app):

    from application import db

    db.create_all()

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
    dimensions = bdd_db.metadata.tables['dimension']
    bdd_db.engine.execute(dimensions.delete())
    uploads = bdd_db.metadata.tables['upload']
    bdd_db.engine.execute(uploads.delete())
    pages = bdd_db.metadata.tables['page']
    bdd_db.engine.execute(pages.delete())
    for tbl in bdd_db.metadata.sorted_tables:
        bdd_db.engine.execute(tbl.delete())

        bdd_db.session.commit()


@pytest.fixture(scope='function')
def stub_topic_page(bdd_db_session):

    page = Page(guid='bdd_topic',
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

    page = Page(guid='bdd_subtopic',
                parent_guid=stub_topic_page.guid,
                page_type='subtopic',
                uri='test-subtopic-page',
                status='DRAFT')

    page.page_json = json.dumps({'title': 'Test subtopic page'})

    bdd_db_session.session.add(page)
    bdd_db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_page(bdd_db_session, stub_subtopic_page):

    page = Page(guid='bdd_measure',
                parent_guid=stub_subtopic_page.guid,
                page_type='measure',
                uri='test-measure-page',
                status='DRAFT')

    bdd_db_session.session.add(page)
    bdd_db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_form_data(stub_measure_page):
    return {'title': "Test Measure Page",
            'short_title': "Measure Page",
            'measure_summary': "Unemployment summary",
            'estimation': "X people are unemployed",
            'type_of_statistic_id': 1,
            'data_source_purpose': 'data_source_purpose',
            'qmi_text': "Quality and Methodology Information",
            'need_to_know': "Need to know this",
            'contact_name': "Jane Doe",
            'contact_email': "janedoe@example.com",
            'contact_phone': '',
            'summary': "Unemployment Sum",
            'data_type': "statistics",
            'frequency': "Quarterly",
            'frequency_id': 1,
            'ethnicity_definition_summary': "Ethnicity information",
            'qmi_url': "http://example.com",
            'guid': "test-measure-page",
            'time_covered': "4 months",
            'geographic_coverage': "United Kingdom",
            'department_source_id': "D10",
            'ethnicity_definition_detail': "Detailed ethnicity information",
            'methodology': "how we measure unemployment",
            'published_date': "15th May 2017",
            'next_update_date': 'Ad hoc',
            'quality_assurance': "Quality assurance",
            'last_update_date': "15th May 2017",
            'revisions': '',
            'source_url': "http://example.com",
            'disclosure_control': "disclosure",
            'further_technical_information': 'further_technical_information',
            'suppression_rules': "suppression rules",
            'related_publications': "related publications",
            'lowest_level_of_geography_id': "UK",
            'publication_date': datetime.now().date().strftime('Y%-%m-%d'),
            'db_version_id': stub_measure_page.db_version_id,
            'type_of_statistic_id': 1
            }

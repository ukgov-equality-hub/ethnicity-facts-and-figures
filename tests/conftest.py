import os
import pytest

from slugify import slugify

from application.config import TestConfig
from application.factory import create_app
from application.cms.models import Page, Meta
from application.auth.models import User


@pytest.fixture(scope='session')
def app(request):
    _app = create_app(TestConfig)

    ctx = _app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return _app


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def db(app):
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

    Migrate(app, db)
    Manager(db, MigrateCommand)
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    ALEMBIC_CONFIG = os.path.join(BASE_DIR, 'migrations')
    config = Config(ALEMBIC_CONFIG + '/alembic.ini')
    config.set_main_option("script_location", ALEMBIC_CONFIG)

    with app.app_context():
        upgrade(config, 'head')

    yield db

    db.session.remove()
    db.get_engine(app).dispose()


@pytest.fixture(scope='function')
def db_session(db):
    yield db

    db.session.remove()

    # this deletes any data in tables, but if you want to start from scratch (i.e. migrations etc, drop everything)
    for tbl in db.metadata.sorted_tables:
        db.engine.execute(tbl.delete())

    db.session.commit()


@pytest.fixture(scope='function')
def mock_user(db, db_session):
    user = User(email='test@example.com', password='password123')
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def mock_page_service_get_pages(mocker):
    return mocker.patch('application.cms.page_service.page_service.get_pages', return_value={})


@pytest.fixture(scope='function')
def stub_topic_page():
    meta = Meta(guid='test-topic-page', uri='test-topic-page', parent=None, page_type='topic')
    page = Page(title='Test Topic Page', data={}, meta=meta)
    return page


@pytest.fixture(scope='function')
def stub_measure_page():
    data = {'title': "unemployment",
            'location_definition_detail': "UK description detail",
            'location_definition_summary': "UK description summary",
            'measure_summary': "Unemployment summary",
            'estimation': "X people are unemployed",
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
            'guid': "measure_unemployment",
            'time_covered': "4 months",
            'geographic_coverage': "United Kingdom",
            'department_source': "DWP",
            'ethnicity_definition_detail': "Detailed ethnicity information",
            'methodology': "how we measure unemployment",
            'population_or_sample': "all",
            'keywords': "['X', 'Y', 'Z']",
            'published_date': "15th May 2017",
            'next_update_date': 'Ad hoc',
            'quality_assurance': "Quality assurance",
            'last_update_date': "15th May 2017",
            'revisions': '',
            'source_text': "DWP Stats",
            'source_url': "http://example.com",
            'disclosure_control': "disclosure"}
    meta = Meta(guid='test-topic-page', uri=data['title'], parent=None, page_type='topic')
    page = Page(title='Test Topic Page', data=data, meta=meta)
    return page


@pytest.fixture(scope='function')
def mock_create_page(mocker):
    print("Creating page")

    def _create_page(page_type, parent=None, data=None):
        print("In_create_page", data['contact_name'])
        meta = Meta(guid=slugify(data['title']), uri=slugify(data['title']), parent=parent, page_type='measure')
        page = Page(title=data['title'], data=data, meta=meta)
        return page

    return mocker.patch('application.cms.views.page_service.create_page', side_effect=_create_page)


@pytest.fixture(scope='function')
def mock_get_page(mocker, stub_topic_page):
    return mocker.patch('application.cms.views.page_service.get_page', return_value=stub_topic_page)


@pytest.fixture(scope='function')
def mock_reject_page(mocker):
    return mocker.patch('application.cms.views.page_service.reject_page')

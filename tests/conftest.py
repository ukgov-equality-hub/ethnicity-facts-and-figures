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
                'postgresql://postgres@localhost:5439/rdcms_test']
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
def stub_page():
    meta = Meta(guid='test-topic-page', uri='test-topic-page', parent=None, page_type='topic')
    page = Page(title='Test Topic Page', description='Not really important', meta=meta)
    return page


@pytest.fixture(scope='function')
def mock_create_page(mocker):

    def _create_page(page_type, data):
        meta = Meta(guid=slugify(data['title']), uri=slugify(data['title']), parent=None, page_type='topic')
        page = Page(title=data['title'], description=data['description'], meta=meta)
        return page

    return mocker.patch('application.cms.views.page_service.create_page', side_effect=_create_page)


@pytest.fixture(scope='function')
def mock_get_page(mocker, stub_page):
    return mocker.patch('application.cms.views.page_service.get_page', return_value=stub_page)


@pytest.fixture(scope='function')
def mock_reject_page(mocker):
    return mocker.patch('application.cms.views.page_service.reject_page')

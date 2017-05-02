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


@pytest.fixture(scope='function')
def mock_user():
    return User(email='test@example.com')


@pytest.fixture(scope='function')
def mock_page_service_get_pages(mocker):
    return mocker.patch('application.cms.page_service.page_service.get_pages', return_value=[])


@pytest.fixture(scope='function')
def stub_page():
    meta = Meta(uri='test-topic-page', parent=None, page_type='topic')
    page = Page(title='Test Topic Page', description='Not really important', meta=meta)
    return page


@pytest.fixture(scope='function')
def mock_create_page(mocker):

    def _create_page(data):
        meta = Meta(uri=slugify(data['title']), parent=None, page_type='topic')
        page = Page(title=data['title'], description=data['description'], meta=meta)
        return page

    return mocker.patch('application.cms.views.page_service.create_page', side_effect=_create_page)


@pytest.fixture(scope='function')
def mock_get_page(mocker, stub_page):
    return mocker.patch('application.cms.views.page_service.get_page', return_value=stub_page)


@pytest.fixture(scope='function')
def mock_reject_page(mocker):
    return mocker.patch('application.cms.views.page_service.reject_page')

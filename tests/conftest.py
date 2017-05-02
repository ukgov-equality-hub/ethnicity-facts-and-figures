import pytest

from application.config import TestConfig
from application.factory import create_app
from application.cms.models import Page, Meta


@pytest.fixture(scope='session')
def app(request):
    _app = create_app(TestConfig)

    ctx = _app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return _app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def mock_page_service(mocker):
    return mocker.patch('application.cms.page_service.page_service.get_pages', return_value=[])


@pytest.fixture(scope='function')
def stub_page():
    meta = Meta(uri='test-topic-page', parent=None, page_type='topic')
    page = Page(title='Test Topic Page', description='Not really important', meta=meta)
    return page

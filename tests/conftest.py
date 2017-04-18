import pytest

from application.config import TestConfig
from application.factory import create_app


@pytest.fixture(scope='session')
def app(request):
    app = create_app(TestConfig)

    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app.test_client()
import os

import pytest
import requests_mock
import sqlalchemy
from alembic.command import upgrade
from alembic.config import Config
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from application import db as app_db
from application.auth.models import TypeOfUser
from application.cms.classification_service import ClassificationService
from application.cms.scanner_service import ScannerService
from application.cms.upload_service import UploadService
from application.config import TestConfig
from application.factory import create_app
from tests.models import UserFactory
from tests.test_data.chart_and_table import grouped_table, simple_table
from tests.utils import UnmockedRequestException


# ############################################################
# #######################   DATABASE   #######################
# ############################################################

# Runs database migrations once at the start of the test session - required to set up materialized views
@pytest.fixture(scope="session", autouse=True)
def db_migration():
    print("Doing db setup")
    app = create_app(TestConfig)
    Migrate(app, app_db)
    Manager(app_db, MigrateCommand)
    ALEMBIC_CONFIG = os.path.join(os.path.dirname(__file__), "../migrations/alembic.ini")
    config = Config(ALEMBIC_CONFIG)
    config.set_main_option("script_location", "migrations")

    with app.app_context():
        upgrade(config, "head")

    print("Done db setup")


@pytest.fixture(scope="function", autouse=True)
def db_session(db):
    db.session.remove()

    # Remove data from all tables so we have a clean slate at the start of every test
    # This ignores materialized views, which need to be refreshed _inside_ a test function definition so that all of the
    # pytest fixtures in use are captured.
    for tbl in reversed(db.metadata.sorted_tables):
        if tbl.name not in sqlalchemy.inspect(db.engine).get_view_names():
            db.engine.execute(tbl.delete())

    db.session.commit()

    yield db


@pytest.fixture(scope="function", autouse=True)
def _configure_factory_sessions(db_session):
    from tests.models import ALL_FACTORIES

    for factory in ALL_FACTORIES:
        factory._meta.sqlalchemy_session = db_session.session

    yield

    for factory in ALL_FACTORIES:
        factory._meta.sqlalchemy_session = None


@pytest.fixture(scope="module")
def db(app):
    from application import db

    with app.app_context():
        db.create_all()

    yield db

    db.session.remove()
    db.get_engine(app).dispose()


# ##############################################################
# #######################   FLASK APPS   #######################
# ##############################################################


@pytest.fixture(scope="session")
def app(request):
    _app = create_app(TestConfig)

    return _app


@pytest.fixture(scope="function")
def single_use_app():
    """
    A function-scoped app fixture. This should only be used for testing the static site building process, as that
    process requires an app which has not yet handled any requests. This is the case for all management commands, which
    are run on Heroku in unroutable, single-use instances of our app.
    """
    _app = create_app(TestConfig)

    return _app


@pytest.fixture(scope="function")
def test_app_client(app):
    return app.test_client()


# #########################################################
# #######################   USERS   #######################
# #########################################################


@pytest.fixture(scope="function")
def logged_in_admin_user(test_app_client):
    user = UserFactory(user_type=TypeOfUser.ADMIN_USER)
    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id
    return user


@pytest.fixture(scope="function")
def logged_in_dept_user(test_app_client):
    user = UserFactory(user_type=TypeOfUser.DEPT_USER)
    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id
    return user


@pytest.fixture(scope="function")
def logged_in_rdu_user(test_app_client):
    user = UserFactory(user_type=TypeOfUser.RDU_USER)
    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id
    return user


@pytest.fixture(scope="function")
def logged_in_dev_user(test_app_client):
    user = UserFactory(user_type=TypeOfUser.DEV_USER)
    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id
    return user


# ###############################################################################
# #######################   MEASURE, CHART & TABLE DATA   #######################
# ###############################################################################


@pytest.fixture(scope="function")
def stub_measure_data():
    return {
        "title": "Test Measure Page",
        "measure_summary": "Unemployment measure summary",
        "estimation": "X people are unemployed",
        "need_to_know": "Need to know this",
        "summary": "Unemployment Summary\n * This is a summary bullet",
        "qmi_url": "http://www.quality-street.gov.uk",
        "time_covered": "4 months",
        "methodology": "how we measure unemployment",
        "further_technical_information": "Further technical information",
        "suppression_and_disclosure": "Suppression rules and disclosure control",
        "related_publications": "Related publications",
        "internal_edit_summary": "initial version",
        "db_version_id": 1,
        "lowest_level_of_geography_id": "UK",
        "ethnicity_definition_summary": "This is a summary of ethnicity definitions",
    }


@pytest.fixture(scope="function")
def stub_simple_table_object():
    return simple_table()


@pytest.fixture(scope="function")
def stub_grouped_table_object():
    return grouped_table()


# ###################################################################
# #######################   CLASSIFICATIONS   #######################
# ###################################################################


@pytest.fixture(scope="function")
def two_classifications_2A_5A():
    classification_service = ClassificationService()

    classification_service.create_classification_with_values(
        "2A", "Ethnicity", "", "White and other", values=["White", "Other"]
    )
    classification_service.create_classification_with_values(
        "5A",
        "Ethnicity",
        "",
        "ONS 2011 5+1",
        values=["Asian", "Black", "Mixed", "White", "Other"],
        values_as_parent=["BAME", "White"],
    )


# ################################################################
# #######################   MOCK PATCHES   #######################
# ################################################################

# Raise exceptions on _all_ requests made via the `requests` library - prevents accidentally calling external services
# Use this as an explicit fixture and mock out specific requests/responses if you need to test specific calls out
@pytest.fixture(scope="function", autouse=True)
def requests_mocker(app):
    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.request(method=requests_mock.ANY, url=requests_mock.ANY, exc=UnmockedRequestException)
        yield requests_mocker


@pytest.fixture(scope="function")
def mock_request_build(mocker):
    return mocker.patch("application.cms.views.build_service.request_build")


@pytest.fixture(scope="function")
def mock_page_service_mark_measure_version_published(mocker):
    return mocker.patch("application.cms.page_service.page_service.mark_measure_version_published")


@pytest.fixture(scope="function")
def mock_create_and_send_activation_email(mocker):
    return mocker.patch("application.admin.views.create_and_send_activation_email")


@pytest.fixture(scope="function")
def mock_get_measure_download(mocker):
    def get(upload, filename, source):
        return upload.file_name

    return mocker.patch("application.static_site.views.upload_service.get_measure_download", side_effect=get)


@pytest.fixture(scope="function")
def mock_get_csv_data_for_download(mocker):
    return mocker.patch("application.static_site.views.get_csv_data_for_download", return_value="i do not care")


@pytest.fixture(scope="function")
def mock_edit_upload(mocker):
    return mocker.patch("application.cms.views.upload_service.edit_upload")


@pytest.fixture(scope="function")
def mock_delete_upload(mocker):
    return mocker.patch("application.cms.views.upload_service.delete_upload_obj")


@pytest.fixture(scope="function")
def scanner_service_mock(mocker):
    return mocker.patch("application.cms.scanner_service.scanner_service")


# ########################################################################
# #######################   OBJECTS AND SERVICES   #######################
# ########################################################################


@pytest.fixture(scope="function")
def scanner_service(app):
    scanner_service = ScannerService()
    scanner_service.init_app(app)
    scanner_service.enabled = True
    return scanner_service


@pytest.fixture(scope="function")
def upload_service(app):
    upload_service = UploadService()
    upload_service.init_app(app)
    upload_service.enabled = True
    return upload_service

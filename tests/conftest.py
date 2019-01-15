import json
import os
from datetime import datetime

import pytest
import requests_mock
import sqlalchemy
from alembic.command import upgrade
from alembic.config import Config
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from application import db as app_db
from application.auth.models import CAPABILITIES, TypeOfUser, User
from application.cms.classification_service import ClassificationService
from application.cms.models import (
    Chart,
    Classification,
    DataSource,
    Dimension,
    FrequencyOfRelease,
    LowestLevelOfGeography,
    Measure,
    MeasureVersion,
    Organisation,
    Subtopic,
    Table,
    Topic,
    TypeOfStatistic,
    Upload,
)
from application.cms.page_service import PageService
from application.cms.scanner_service import ScannerService
from application.cms.upload_service import UploadService
from application.config import TestConfig
from application.data.standardisers.ethnicity_dictionary_lookup import EthnicityDictionaryLookup
from application.factory import create_app
from tests.test_data.chart_and_table import grouped_table, multi_series_bar_chart, simple_table, single_series_bar_chart
from tests.utils import UnmockedRequestException


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


# Runs database migrations once at the start of the test session - required to set up materialized views
@pytest.fixture(autouse=True, scope="session")
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


# Raise exceptions on _all_ requests made via the `requests` library - prevents accidentally calling external services
# Use this as an explicit fixture and mock out specific requests/responses if you need to test specific calls out
@pytest.fixture(scope="function", autouse=True)
def requests_mocker(app):
    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.request(method=requests_mock.ANY, url=requests_mock.ANY, exc=UnmockedRequestException)
        yield requests_mocker


@pytest.fixture(scope="function")
def test_app_client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def test_app_editor(db_session):
    user = User(email="editor@methods.co.uk", password="password123", active=True)
    user.user_type = TypeOfUser.RDU_USER
    user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def test_app_admin(db_session):
    user = User(email="admin@methods.co.uk", password="password123", active=True)
    user.user_type = TypeOfUser.ADMIN_USER
    user.capabilities = CAPABILITIES[TypeOfUser.ADMIN_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="module")
def db(app):
    from application import db

    with app.app_context():
        db.create_all()

    yield db

    db.session.remove()
    db.get_engine(app).dispose()


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


@pytest.fixture(scope="function")
def mock_admin_user(db_session):
    return _user_of_type(db_session, TypeOfUser.ADMIN_USER)


@pytest.fixture(scope="function")
def mock_dept_user(db_session):
    return _user_of_type(db_session, TypeOfUser.DEPT_USER)


@pytest.fixture(scope="function")
def mock_dev_user(db_session):
    return _user_of_type(db_session, TypeOfUser.DEV_USER)


@pytest.fixture(scope="function")
def mock_rdu_user(db_session):
    return _user_of_type(db_session, TypeOfUser.RDU_USER)


@pytest.fixture(scope="function")
def mock_logged_in_admin_user(mock_admin_user, test_app_client):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id
    return mock_admin_user


@pytest.fixture(scope="function")
def mock_logged_in_dept_user(mock_dept_user, test_app_client):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id
    return mock_dept_user


@pytest.fixture(scope="function")
def mock_logged_in_rdu_user(mock_rdu_user, test_app_client):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id
    return mock_rdu_user


# To use this fixture pass in a TypeOfUser as request.param
@pytest.fixture(scope="function")
def mock_user(db_session, request):
    return _user_of_type(db_session, request.param)


def _user_of_type(db_session, type_of_user):
    user = User(email=f"{type_of_user.name}@eff.service.gov.uk", password="password123", active=True)
    user.user_type = type_of_user
    user.capabilities = CAPABILITIES[type_of_user]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def stub_compatible_topic(db_session):
    topic = Topic(id=98, slug="test", title="Test topic page", description="", additional_description="")
    db_session.session.add(topic)
    db_session.session.commit()
    return topic


# TODO: Delete these stubs after using new hierarchy tables.
@pytest.fixture(scope="function")
def stub_topic_page(db_session, stub_home_page, stub_compatible_topic):
    page = MeasureVersion(
        id=98,
        guid="topic_test",
        parent_id=97,
        parent_guid="homepage",
        page_type="topic",
        slug="test",
        status="DRAFT",
        title="Test topic page",
        version="1.0",
    )

    page.page_json = json.dumps({"guid": "topic_test", "title": "Test topic page"})

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_compatible_subtopic(db_session, stub_compatible_topic):
    subtopic = Subtopic(
        id=99, slug="example", title="Test subtopic page", position=0, topic_id=stub_compatible_topic.id
    )
    db_session.session.add(subtopic)
    db_session.session.commit()
    return subtopic


# TODO: Delete these stubs after using new hierarchy tables.
@pytest.fixture(scope="function")
def stub_subtopic_page(db_session, stub_topic_page, stub_compatible_subtopic):
    page = MeasureVersion(
        id=99,
        guid="subtopic_example",
        parent_id=stub_topic_page.id,
        parent_guid=stub_topic_page.guid,
        parent_version=stub_topic_page.version,
        page_type="subtopic",
        slug="example",
        status="DRAFT",
        title="Test subtopic page",
        version="1.0",
    )

    page.page_json = json.dumps({"guid": "subtopic_example", "title": "Test subtopic page"})

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_home_page(db_session):
    page = MeasureVersion(
        id=97,
        guid="homepage",
        page_type="homepage",
        slug="/",
        status="DRAFT",
        title="Test homepage page",
        version="1.0",
    )

    db_session.session.add(page)
    db_session.session.commit()
    return page


# TODO: Delete these stubs after using new hierarchy tables.
@pytest.fixture(scope="function")
def stub_sandbox_topic_page(db_session):
    page = MeasureVersion(
        id=101,
        guid="sandbox_topic_test",
        page_type="topic",
        slug="test-sandbox",
        status="DRAFT",
        title="Test sandbox topic page",
        version="1.0",
    )
    topic = Topic(id=page.id, slug=page.slug, title=page.title)

    db_session.session.add(page)
    db_session.session.add(topic)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_frequency(db_session):
    frequency = FrequencyOfRelease(id=1, description="Quarterly", position=1)
    db_session.session.add(frequency)
    db_session.session.commit()
    return frequency


@pytest.fixture(scope="function")
def stub_dept(db_session):
    dept = Organisation(id="D10", name="Department for Work and Pensions", organisation_type="MINISTERIAL_DEPARTMENT")

    db_session.session.add(dept)
    db_session.session.commit()
    return dept


@pytest.fixture(scope="function")
def stub_geography(db_session):
    geography = LowestLevelOfGeography(name="UK", position=0)
    db_session.session.add(geography)
    db_session.session.commit()
    return geography


@pytest.fixture(scope="function")
def stub_type_of_statistic(db_session):
    type_of_statistic = TypeOfStatistic(id=1, internal="National", external="National", position=1)
    db_session.session.add(type_of_statistic)
    db_session.session.commit()
    return type_of_statistic


@pytest.fixture(scope="function")
def stub_organisations(db_session):
    organisation = Organisation(
        id="D10",
        name="Department for Work and Pensions",
        other_names=[],
        abbreviations=["DWP"],
        organisation_type="MINISTERIAL_DEPARTMENT",
    )
    db_session.session.add(organisation)
    db_session.session.commit()
    return organisation


@pytest.fixture(scope="function")
def stub_data_source(db_session, stub_organisations, stub_type_of_statistic, stub_frequency):
    data_source = DataSource(
        title="DWP Stats",
        type_of_data=["SURVEY"],
        type_of_statistic_id=stub_type_of_statistic.id,
        publisher_id=stub_organisations.id,
        source_url="http://dwp.gov.uk",
        publication_date="15th May 2017",
        note_on_corrections_or_updates="Note on corrections or updates",
        frequency_of_release_id=stub_frequency.id,
        purpose="Purpose of data source",
    )
    db_session.session.add(data_source)
    db_session.session.commit()

    return data_source


@pytest.fixture(scope="function")
def stub_compatible_measure(db_session, stub_compatible_subtopic):
    measure = Measure(slug="test-measure-page", position=0)
    measure.subtopics = [stub_compatible_subtopic]

    db_session.session.add(measure)
    db_session.session.commit()

    return measure


# TODO: Delete these stubs after using new hierarchy tables.
@pytest.fixture(scope="function")
def stub_measure_page(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_geography,
    stub_data_source,
    stub_compatible_measure,
):
    page = MeasureVersion(
        id=100,
        guid="test-measure-page",
        parent_id=stub_subtopic_page.id,
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        slug="test-measure-page",
        status="DRAFT",
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=True,
    )
    page.measure_id = (
        stub_compatible_measure.id
    )  # Duplicating page ID for simplicity during migration to new data model

    for key, val in stub_measure_data.items():
        if key == "published_at":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    page.data_sources = [stub_data_source]

    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_published_measure_page(
    db_session, stub_subtopic_page, stub_measure_data, stub_frequency, stub_geography, stub_data_source
):  # TODO: Delete these stubs after using new hierarchy tables.
    page = MeasureVersion(
        id=_get_random_unused_measure_version_id(),
        guid="test-published-measure-page",
        parent_id=stub_subtopic_page.id,
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        slug="test-published-measure-page",
        status="APPROVED",
        published=True,
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=True,
    )
    measure = Measure(id=page.id, slug=page.slug, position=page.position, reference=page.internal_reference)
    measure.subtopics = [Subtopic.query.get(stub_subtopic_page.id)]
    page.measure_id = page.id  # Duplicating page ID for simplicity during migration to new data model

    for key, val in stub_measure_data.items():
        if key == "published_at":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    page.data_sources = [stub_data_source]

    db_session.session.add(measure)
    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_measure_data():
    return {
        "title": "Test Measure Page",
        "short_title": "Measure Page",
        "measure_summary": "Unemployment measure summary",
        "estimation": "X people are unemployed",
        "type_of_statistic": "type of statistic",
        "qmi_text": "Quality and Methodology Information",
        "need_to_know": "Need to know this",
        "summary": "Unemployment Summary\n * This is a summary bullet",
        "frequency": "Quarterly",
        "qmi_url": "http://www.quality-street.gov.uk",
        "time_covered": "4 months",
        "geographic_coverage": "United Kingdom",
        "ethnicity_definition_detail": "Detailed ethnicity information",
        "methodology": "how we measure unemployment",
        "next_update_date": "Ad hoc",
        "quality_assurance": "Quality assurance",
        "revisions": "",
        "further_technical_information": "Further technical information",
        "suppression_and_disclosure": "Suppression rules and disclosure control",
        "related_publications": "Related publications",
        "published_at": datetime.now().date().strftime("%Y-%m-%d"),
        "internal_edit_summary": "initial version",
        "db_version_id": 1,
        "lowest_level_of_geography_id": "UK",
        "ethnicity_definition_summary": "This is a summary of ethnicity definitions",
    }


@pytest.fixture(scope="function")
def stub_multiversion_measure(db_session, stub_subtopic_page):
    subtopic = Subtopic.query.filter_by(slug=stub_subtopic_page.slug).one()

    measure = Measure(slug="multiversion-measure", position=1)
    measure.subtopics = [subtopic]

    db_session.session.add(measure)
    db_session.session.commit()
    return measure


@pytest.fixture(scope="function")
def stub_measure_page_one_of_three(
    db_session,
    stub_subtopic_page,
    stub_multiversion_measure,
    stub_measure_data,
    stub_frequency,
    stub_geography,
    stub_data_source,
):  # TODO: Delete these stubs after using new hierarchy tables.
    page = MeasureVersion(
        id=201,
        guid="test-multiversion-measure-page-1-of-3",
        parent_id=stub_subtopic_page.id,
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        slug="test-multiversion-measure-page-1-of-3",
        status="APPROVED",
        published=True,
        version="1.0",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=False,
        measure_id=stub_multiversion_measure.id,
    )

    for key, val in stub_measure_data.items():
        if key == "published_at":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    page.data_sources = [stub_data_source]
    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_measure_page_two_of_three(
    db_session,
    stub_subtopic_page,
    stub_multiversion_measure,
    stub_measure_data,
    stub_frequency,
    stub_geography,
    stub_data_source,
):  # TODO: Delete these stubs after using new hierarchy tables.
    page = MeasureVersion(
        id=202,
        guid="test-multiversion-measure-page-2-of-3",
        parent_id=stub_subtopic_page.id,
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        slug="test-multiversion-measure-page-2-of-3",
        status="APPROVED",
        published=True,
        version="2.0",
        internal_edit_summary="internal_edit_summary_v2",
        external_edit_summary="external_edit_summary_v2",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=False,
        measure_id=stub_multiversion_measure.id,
    )

    for key, val in stub_measure_data.items():
        if key == "published_at":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    page.data_sources = [stub_data_source]
    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_measure_page_three_of_three(
    db_session,
    stub_subtopic_page,
    stub_multiversion_measure,
    stub_measure_data,
    stub_frequency,
    stub_geography,
    stub_data_source,
):  # TODO: Delete these stubs after using new hierarchy tables.
    page = MeasureVersion(
        id=203,
        guid="test-multiversion-measure-page-3-of-3",
        parent_id=stub_subtopic_page.id,
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        slug="test-multiversion-measure-page-3-of-3",
        status="DRAFT",
        published=False,
        version="2.1",
        internal_edit_summary="internal_edit_summary_v3",
        external_edit_summary="external_edit_summary_v3",
        area_covered=["ENGLAND"],
        lowest_level_of_geography=stub_geography,
        latest=True,
        measure_id=stub_multiversion_measure.id,
    )

    for key, val in stub_measure_data.items():
        if key == "published_at":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    page.data_sources = [stub_data_source]
    db_session.session.add(page)
    db_session.session.commit()

    return page


@pytest.fixture(scope="function")
def stub_page_with_dimension(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
    )

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_dimension_and_chart(db_session, stub_measure_page, two_classifications_2A_5A):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
    )
    db_chart = Chart(classification_id="2A", includes_parents=False, includes_all=True, includes_unknown=False)
    db_session.session.flush()

    from tests.test_data.chart_and_table import chart
    from tests.test_data.chart_and_table import chart_source_data

    db_dimension.chart = chart
    db_dimension.chart_source_data = chart_source_data
    db_dimension.chart_2_source_data = chart_source_data
    db_dimension.dimension_chart = db_chart
    db_dimension.update_dimension_classification_from_chart_or_table()

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_dimension_and_chart_and_table(db_session, stub_page_with_dimension_and_chart):
    from tests.test_data.chart_and_table import table
    from tests.test_data.chart_and_table import table_source_data

    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    db_table = Table(classification_id="5A", includes_parents=True, includes_all=False, includes_unknown=True)
    db_session.session.flush()

    dimension.table = table
    dimension.table_source_data = table_source_data
    dimension.table_2_source_data = table_source_data
    dimension.dimension_table = db_table
    dimension.update_dimension_classification_from_chart_or_table()

    db_session.session.add(stub_page_with_dimension_and_chart)
    db_session.session.commit()
    return stub_page_with_dimension_and_chart


@pytest.fixture(scope="function")
def stub_page_with_upload_and_dimension_and_chart_and_table(db_session, stub_page_with_dimension_and_chart):
    from tests.test_data.chart_and_table import table
    from tests.test_data.chart_and_table import table_source_data

    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    dimension.table = table
    dimension.table_source_data = table_source_data

    upload = Upload(
        guid="test-measure-page-upload",
        title="Test measure page data",
        file_name="test-measure-page-data.csv",
        description="This is a test measure page upload with loads of source data",
        size="1024",
        measure_version_id=stub_page_with_dimension_and_chart.id,
        page_id=stub_page_with_dimension_and_chart.guid,
        page_version=stub_page_with_dimension_and_chart.version,
    )

    db_session.session.add(stub_page_with_dimension_and_chart)
    db_session.session.add(upload)
    db_session.session.commit()
    return stub_page_with_dimension_and_chart


@pytest.fixture(scope="function")
def stub_page_with_simple_table(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
        table=simple_table(),
    )

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_grouped_table(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
        table=grouped_table(),
    )

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_single_series_bar_chart(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
        chart=single_series_bar_chart(),
    )

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_multi_series_bar_chart(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
        chart=multi_series_bar_chart(),
    )

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_simple_table_object():
    return simple_table()


@pytest.fixture(scope="function")
def stub_grouped_table_object():
    return grouped_table()


@pytest.fixture(scope="function")
def stub_classification(db_session):
    db_classification = Classification(id="stub_classification")
    db_session.session.add(db_classification)
    db_session.session.commit()
    return db_classification


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


@pytest.fixture(scope="function")
def mock_request_build(mocker):
    return mocker.patch("application.cms.views.build_service.request_build")


@pytest.fixture(scope="function")
def mock_new_page_service_mark_measure_version_published(mocker):
    return mocker.patch("application.cms.new_page_service.new_page_service.mark_measure_version_published")


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


@pytest.fixture(scope="session")
def dictionary_lookup():
    return EthnicityDictionaryLookup(
        "./tests/test_data/test_dictionary_lookup/test_ethnicity_lookup.csv",
        default_values=TestConfig.DICTIONARY_LOOKUP_DEFAULTS,
    )


@pytest.fixture(scope="function")
def scanner_service(app):
    scanner_service = ScannerService()
    scanner_service.init_app(app)
    scanner_service.enabled = True
    return scanner_service


@pytest.fixture(scope="function")
def scanner_service_mock(mocker):
    return mocker.patch("application.cms.scanner_service.scanner_service")


@pytest.fixture(scope="function")
def upload_service(app):
    upload_service = UploadService()
    upload_service.init_app(app)
    upload_service.enabled = True
    return upload_service


@pytest.fixture(scope="function")
def page_service(app):
    page_service = PageService()
    page_service.init_app(app)
    return page_service


@pytest.fixture(scope="function")
def stub_topic(db_session):
    topic = Topic(
        slug="test",
        title="Test topic page",
        description="A topic for testing",
        additional_description="This is a topic to use in tests",
    )

    db_session.session.add(topic)
    db_session.session.commit()
    return topic


@pytest.fixture(scope="function")
def stub_subtopic(db_session, stub_topic):
    subtopic = Subtopic(slug="example", title="Test subtopic page", position=1, topic_id=stub_topic.id)

    db_session.session.add(subtopic)
    db_session.session.commit()
    return subtopic


@pytest.fixture(scope="function")
def stub_measure_1(db_session, stub_subtopic):
    measure = Measure(slug="test-measure-1", position=1, reference="RDU TEST 1")
    measure.subtopics = [stub_subtopic]

    db_session.session.add(measure)
    db_session.session.commit()
    return measure


@pytest.fixture(scope="function")
def stub_measure_2(db_session, stub_subtopic):
    measure = Measure(slug="test-measure-2", position=2, reference="RDU TEST 2")
    measure.subtopics = [stub_subtopic]

    db_session.session.add(measure)
    db_session.session.commit()
    return measure


@pytest.fixture(scope="function")
def stub_measure_version(db_session, stub_measure_1):
    measure_version = MeasureVersion(
        id=100,
        guid="test-measure-version",
        measure_id=stub_measure_1.id,
        slug="test-measure-version",
        title="Test Measure Page",
        status="DRAFT",
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["ENGLAND"],
        latest=True,
    )

    db_session.session.add(measure_version)
    db_session.session.commit()

    return measure_version


@pytest.fixture(scope="function")
def stub_upload(db_session, stub_measure_version):
    upload = Upload(
        guid="test-upload",
        title="Test measure version data",
        file_name="test-measure-version-data.csv",
        description="This is a test upload",
        size="1024",
        page=stub_measure_version,
    )

    db_session.session.add(upload)
    db_session.session.commit()
    return upload


@pytest.fixture(scope="function")
def stub_dimension(db_session, stub_measure_version):
    dimension = Dimension(
        guid="test-dimension", title="Test dimension", time_period="timeperiod", page=stub_measure_version
    )

    db_session.session.add(dimension)
    db_session.session.commit()
    return dimension


def _get_random_unused_measure_version_id():
    from random import randint

    id = randint(1, 99999)
    while MeasureVersion.query.filter_by(id=id).first() is not None:
        id = randint(1, 99999)
    return id

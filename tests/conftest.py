import json
import os

import pytest
from alembic.command import upgrade
from alembic.config import Config
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from application import db as app_db
from application.auth.models import *
from application.cms.data_utils import Harmoniser
from application.cms.models import *
from application.config import TestConfig
from application.factory import create_app
from tests.test_data.chart_and_table import simple_table, grouped_table, single_series_bar_chart, multi_series_bar_chart


@pytest.fixture(scope="session")
def app(request):
    _app = create_app(TestConfig)

    ctx = _app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
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

    db.create_all()

    yield db

    db.session.remove()
    db.get_engine(app).dispose()


@pytest.fixture(scope="function")
def db_session(db):
    yield db

    db.session.remove()

    # this deletes any data in tables, but if you want to start from scratch (i.e. migrations etc, drop everything)

    # delete many-to-many tables first
    association = db.metadata.tables["association"]
    db.engine.execute(association.delete())
    parent_association = db.metadata.tables["parent_association"]
    db.engine.execute(parent_association.delete())
    dimension_category = db.metadata.tables["dimension_categorisation"]
    db.engine.execute(dimension_category.delete())
    dimensions = db.metadata.tables["dimension"]
    db.engine.execute(dimensions.delete())
    uploads = db.metadata.tables["upload"]
    db.engine.execute(uploads.delete())
    user_page = db.metadata.tables["user_page"]
    db.engine.execute(user_page.delete())
    pages = db.metadata.tables["page"]
    db.engine.execute(pages.delete())

    insp = sqlalchemy.inspect(db.engine)
    views = insp.get_view_names()
    for tbl in db.metadata.sorted_tables:
        if tbl.name not in views:
            db.engine.execute(tbl.delete())

    db.session.commit()


@pytest.fixture(scope="function")
def mock_user(db_session):
    user = User(email="test@example.gov.uk", password="password123", active=True)
    user.user_type = TypeOfUser.RDU_USER
    user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def mock_admin_user(db_session):
    user = User(email="admin@example.gov.uk", password="password123", active=True)
    user.user_type = TypeOfUser.ADMIN_USER
    user.capabilities = CAPABILITIES[TypeOfUser.ADMIN_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def mock_dept_user(db_session):
    user = User(email="dept_user", password="password123", active=True)
    user.user_type = TypeOfUser.DEPT_USER
    user.capabilities = CAPABILITIES[TypeOfUser.DEPT_USER]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope="function")
def stub_topic_page(db_session):
    page = Page(
        guid="topic_test",
        parent_guid="homepage",
        page_type="topic",
        uri="test",
        status="DRAFT",
        title="Test topic page",
        version="1.0",
    )

    page.page_json = json.dumps({"guid": "topic_test", "title": "Test topic page"})

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_subtopic_page(db_session, stub_topic_page):
    page = Page(
        guid="subtopic_example",
        parent_guid=stub_topic_page.guid,
        parent_version=stub_topic_page.version,
        page_type="subtopic",
        uri="example",
        status="DRAFT",
        title="Test subtopic page",
        version="1.0",
    )

    page.page_json = json.dumps({"guid": "subtopic_example", "title": "Test subtopic page"})

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_home_page(db_session, stub_topic_page, stub_sandbox_topic_page):
    page = Page(
        guid="homepage", page_type="homepage", uri="/", status="DRAFT", title="Test homepage page", version="1.0"
    )

    page.children.append(stub_topic_page)
    # note stub_sandbox_topic_page is not hooked into homepage
    # and we can assert only one topic on homepage in tests

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_sandbox_topic_page(db_session):
    page = Page(
        guid="sandbox_topic_test",
        page_type="topic",
        uri="test-sandbox",
        status="DRAFT",
        title="Test sandbox topic page",
        version="1.0",
    )

    db_session.session.add(page)
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
        id=1,
        name="Department for Work and Pensions",
        other_names=[],
        abbreviations=["DWP"],
        organisation_type="MINISTERIAL_DEPARTMENT",
    )
    db_session.session.add(organisation)
    db_session.session.commit()
    return organisation


@pytest.fixture(scope="function")
def stub_measure_page(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_dept,
    stub_geography,
    stub_type_of_statistic,
    stub_organisations,
):
    page = Page(
        guid="test-measure-page",
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        uri="test-measure-page",
        status="DRAFT",
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["UK"],
        department_source=stub_dept,
        lowest_level_of_geography=stub_geography,
        latest=True,
        type_of_statistic_id=stub_type_of_statistic.id,
    )

    for key, val in stub_measure_data.items():
        if key == "publication_date":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_published_measure_page(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_dept,
    stub_geography,
    stub_type_of_statistic,
    stub_organisations,
):
    page = Page(
        guid="test-published-measure-page",
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        uri="test-published-measure-page",
        status="APPROVED",
        published=True,
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["UK"],
        department_source=stub_dept,
        lowest_level_of_geography=stub_geography,
        latest=True,
        type_of_statistic_id=stub_type_of_statistic.id,
    )

    for key, val in stub_measure_data.items():
        if key == "publication_date":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)

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
        "data_source_purpose": "Purpose of data source",
        "qmi_text": "Quality and Methodology Information",
        "need_to_know": "Need to know this",
        "contact_name": "Jane Doe",
        "contact_email": "janedoe@example.com",
        "contact_phone": "",
        "summary": "Unemployment Summary",
        "frequency": "Quarterly",
        "frequency_id": 1,
        "qmi_url": "http://www.quality-street.gov.uk",
        "time_covered": "4 months",
        "geographic_coverage": "United Kingdom",
        "ethnicity_definition_detail": "Detailed ethnicity information",
        "methodology": "how we measure unemployment",
        "published_date": "15th May 2017",
        "next_update_date": "Ad hoc",
        "quality_assurance": "Quality assurance",
        "revisions": "",
        "source_text": "DWP Stats",
        "source_url": "http://dwp.gov.uk",
        "further_technical_information": "Further technical information",
        "suppression_and_disclosure": "Suppression rules and disclosure control",
        "related_publications": "Related publications",
        "publication_date": datetime.now().date().strftime("%Y-%m-%d"),
        "internal_edit_summary": "initial version",
        "db_version_id": 1,
        "lowest_level_of_geography_id": "UK",
        "note_on_corrections_or_updates": "Note on corrections or updates",
        "ethnicity_definition_summary": "This is a summary of ethnicity definitions",
        "type_of_data": ["SURVEY"],
    }


@pytest.fixture(scope="function")
def stub_measure_page_one_of_two(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_dept,
    stub_geography,
    stub_type_of_statistic,
    stub_organisations,
):
    page = Page(
        guid="test-published-measure-page",
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        uri="test-published-measure-page",
        status="APPROVED",
        published=True,
        version="1.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["UK"],
        department_source=stub_dept,
        lowest_level_of_geography=stub_geography,
        latest=False,
        type_of_statistic_id=stub_type_of_statistic.id,
    )
    for key, val in stub_measure_data.items():
        if key == "publication_date":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)
    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def stub_measure_page_two_of_two(
    db_session,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_dept,
    stub_geography,
    stub_type_of_statistic,
    stub_organisations,
):
    page = Page(
        guid="test-published-measure-page",
        parent_guid=stub_subtopic_page.guid,
        parent_version=stub_subtopic_page.version,
        page_type="measure",
        uri="test-published-measure-page",
        status="APPROVED",
        published=True,
        version="2.0",
        internal_edit_summary="internal_edit_summary",
        external_edit_summary="external_edit_summary",
        area_covered=["UK"],
        department_source=stub_dept,
        lowest_level_of_geography=stub_geography,
        latest=True,
        type_of_statistic_id=stub_type_of_statistic.id,
    )
    for key, val in stub_measure_data.items():
        if key == "publication_date":
            val = datetime.strptime(val, "%Y-%m-%d")
        setattr(page, key, val)
    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope="function")
def mock_create_page(mocker, stub_measure_page):
    def _create_page(page_type, parent, data, user):
        return stub_measure_page

    return mocker.patch("application.cms.views.page_service.create_page", side_effect=_create_page)


@pytest.fixture(scope="function")
def mock_get_page(mocker, stub_topic_page, stub_measure_page):
    def _get_page(guid):
        if guid == "test-measure-page":
            return stub_measure_page
        else:
            return stub_topic_page

    return mocker.patch("application.cms.views.page_service.get_page", side_effect=_get_page)


@pytest.fixture(scope="function")
def mock_get_measure_page(mocker, stub_measure_page):
    return mocker.patch("application.cms.views.page_service.get_page", return_value=stub_measure_page)


@pytest.fixture(scope="function")
def mock_reject_page(mocker, stub_topic_page):
    return mocker.patch("application.cms.views.page_service.reject_page", return_value=stub_topic_page)


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
def stub_page_with_dimension_and_chart(db_session, stub_measure_page):
    db_dimension = Dimension(
        guid="stub_dimension",
        title="stub dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
    )

    from tests.test_data.chart_and_table import chart
    from tests.test_data.chart_and_table import chart_source_data

    db_dimension.chart = chart
    db_dimension.chart_source_data = chart_source_data

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope="function")
def stub_page_with_dimension_and_chart_and_table(db_session, stub_page_with_dimension_and_chart):
    from tests.test_data.chart_and_table import table
    from tests.test_data.chart_and_table import table_source_data

    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    dimension.table = table
    dimension.table_source_data = table_source_data

    db_session.session.add(stub_page_with_dimension_and_chart)
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
def stub_page_with_single_series_bar_chart(db_session, stub_measure_page):
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
def stub_categorisation(db_session):
    db_categorisation = Categorisation(code="stub_categorisation")
    db_session.session.add(db_categorisation)
    db_session.session.commit()
    return db_categorisation


@pytest.fixture(scope="function")
def mock_request_build(mocker):
    return mocker.patch("application.cms.views.build_service.request_build")


@pytest.fixture(scope="function")
def mock_page_service_mark_page_published(mocker):
    return mocker.patch("application.cms.page_service.page_service.mark_page_published")


@pytest.fixture(scope="function")
def mock_create_and_send_activation_email(mocker):
    return mocker.patch("application.admin.views.create_and_send_activation_email")


@pytest.fixture(scope="function")
def mock_get_measure_download(mocker):
    def get(upload, filename, source):
        return upload.file_name

    return mocker.patch("application.static_site.views.upload_service.get_measure_download", side_effect=get)


@pytest.fixture(scope="function")
def mock_get_content_with_metadata(mocker):
    return mocker.patch("application.static_site.views.get_content_with_metadata", return_value="i do not care")


@pytest.fixture(scope="function")
def mock_edit_upload(mocker):
    return mocker.patch("application.cms.views.upload_service.edit_upload")


@pytest.fixture(scope="function")
def mock_delete_upload(mocker):
    return mocker.patch("application.cms.views.upload_service.delete_upload_obj")


@pytest.fixture(scope="session")
def harmoniser():
    return Harmoniser(
        "./tests/test_data/test_lookups/test_ethnicity_lookup.csv", default_values=TestConfig.HARMONISER_DEFAULTS
    )

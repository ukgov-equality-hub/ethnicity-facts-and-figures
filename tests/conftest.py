import pytest
import json

from application.config import TestConfig
from application.factory import create_app

from application.auth.models import *
from application.cms.models import *
from tests.test_data.chart_and_table import simple_table, grouped_table, single_series_bar_chart, multi_series_bar_chart


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
def test_app_client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def test_app_editor(db_session):
    user = User(email='editor@methods.co.uk', password='password123', active=True)
    role = Role(name='INTERNAL_USER', description='An internal user')
    user.roles = [role]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='module')
def db(app):

    # TODO: Improve this
    test_dbs = ['postgresql://localhost/rdcms_test',
                'postgres://ubuntu:ubuntu@127.0.0.1:5433/circle_test',
                'postgresql://postgres@localhost:5439/rdcms_test',
                'postgresql://postgres@localhost:5432/rdcms_test',
                'postgres://ubuntu:ubuntu@127.0.0.1:5433/circle_test']

    from application import db
    assert str(db.engine.url) in test_dbs, 'only run tests against test db'
    db.create_all()

    yield db

    db.session.remove()
    db.get_engine(app).dispose()


@pytest.fixture(scope='function')
def db_session(db):
    yield db

    db.session.remove()

    # this deletes any data in tables, but if you want to start from scratch (i.e. migrations etc, drop everything)
    # delete roles_users first
    roles_users = db.metadata.tables['roles_users']
    db.engine.execute(roles_users.delete())
    dimensions = db.metadata.tables['db_dimension']
    db.engine.execute(dimensions.delete())
    for tbl in db.metadata.sorted_tables:
        db.engine.execute(tbl.delete())

    db.session.commit()


@pytest.fixture(scope='function')
def mock_user(db_session):
    role = Role(name='INTERNAL_USER', description='An internal user')
    user = User(email='test@example.com', password='password123', active=True)
    user.roles = [role]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def mock_admin_user(db_session):
    internal_role = Role(name='INTERNAL_USER', description='An internal user')
    admin = Role(name='ADMIN', description='An admin user')
    user = User(email='dept_user', password='password123', active=True)
    user.roles = [internal_role, admin]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def mock_dept_user(db_session):
    role = Role(name='DEPARTMENTAL_USER', description='A departmental user')
    user = User(email='dept_user', password='password123', active=True)
    user.roles = [role]
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture(scope='function')
def mock_page_service_get_pages_by_type(mocker):
    return mocker.patch('application.cms.page_service.page_service.get_pages_by_type', return_value=[])


@pytest.fixture(scope='function')
def stub_topic_page(db_session):

    page = DbPage(guid='topic_test',
                  parent_guid=None,
                  page_type='topic',
                  uri='test',
                  status='DRAFT',
                  subtopics=['subtopic_example'],
                  title='Test topic page',
                  version='1.0')

    page.page_json = json.dumps({'guid': 'topic_test',
                                 'title': 'Test topic page',
                                 'subtopics': ['subtopic_example']})

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_subtopic_page(db_session, stub_topic_page):

    page = DbPage(guid='subtopic_example',
                  parent_guid=stub_topic_page.guid,
                  parent_version=stub_topic_page.version,
                  page_type='subtopic',
                  uri='example',
                  status='DRAFT',
                  title='Test subtopic page',
                  version='1.0')

    page.page_json = json.dumps({'guid': 'subtopic_example',
                                 'title': 'Test subtopic page'})

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_page(db_session, stub_subtopic_page, stub_measure_data):

    page = DbPage(guid='test-measure-page',
                  parent_guid=stub_subtopic_page.guid,
                  parent_version=stub_subtopic_page.version,
                  page_type='measure',
                  uri='test-measure-page',
                  status='DRAFT',
                  version='1.0',
                  internal_edit_summary='internal_edit_summary',
                  external_edit_summary='external_edit_summary')

    for key, val in stub_measure_data.items():
        if key == 'publication_date':
            val = datetime.strptime(val, '%Y-%m-%d')
        setattr(page, key, val)

    db_session.session.add(page)
    db_session.session.commit()
    return page


@pytest.fixture(scope='function')
def stub_measure_data():
    return {
        'title': "Test Measure Page",
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
        'publication_date': datetime.now().date().strftime('%Y-%m-%d'),
        'internal_edit_summary': "initial version"
    }


@pytest.fixture(scope='function')
def stub_measure_form_data():
    dict = stub_measure_data()
    dict['guid'] = 'test-measure-page'
    return dict


@pytest.fixture(scope='function')
def mock_create_page(mocker, stub_measure_page):

    def _create_page(page_type, parent, data, user):
        return stub_measure_page

    return mocker.patch('application.cms.views.page_service.create_page', side_effect=_create_page)


@pytest.fixture(scope='function')
def mock_get_page(mocker, stub_topic_page, stub_measure_page):

    def _get_page(guid):
        if guid == 'test-measure-page':
            return stub_measure_page
        else:
            return stub_topic_page

    return mocker.patch('application.cms.views.page_service.get_page', side_effect=_get_page)


@pytest.fixture(scope='function')
def mock_get_measure_page(mocker, stub_measure_page):
    return mocker.patch('application.cms.views.page_service.get_page', return_value=stub_measure_page)


@pytest.fixture(scope='function')
def mock_reject_page(mocker, stub_topic_page):
    return mocker.patch('application.cms.views.page_service.reject_page', return_value=stub_topic_page)


@pytest.fixture(scope='function')
def stub_page_with_dimension_and_chart(db_session, stub_measure_page):

    db_dimension = DbDimension(guid='stub_dimension',
                               title='stub dimension',
                               time_period='stub_timeperiod',
                               measure=stub_measure_page,
                               position=stub_measure_page.dimensions.count())

    from tests.test_data.chart_and_table import chart
    from tests.test_data.chart_and_table import chart_source_data

    db_dimension.chart = chart
    db_dimension.chart_source_data = chart_source_data

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope='function')
def stub_page_with_dimension_and_chart_and_table(db_session, stub_page_with_dimension_and_chart):

    from tests.test_data.chart_and_table import table
    from tests.test_data.chart_and_table import table_source_data

    dimension = stub_page_with_dimension_and_chart.dimensions[0]

    dimension.table = table
    dimension.table_source_data = table_source_data

    db_session.session.add(stub_page_with_dimension_and_chart)
    db_session.session.commit()
    return stub_page_with_dimension_and_chart


@pytest.fixture(scope='function')
def stub_page_with_simple_table(db_session, stub_measure_page):

    db_dimension = DbDimension(guid='stub_dimension',
                               title='stub dimension',
                               time_period='stub_timeperiod',
                               measure=stub_measure_page,
                               position=stub_measure_page.dimensions.count(),
                               table=simple_table())

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope='function')
def stub_page_with_grouped_table(db_session, stub_measure_page):

    db_dimension = DbDimension(guid='stub_dimension',
                               title='stub dimension',
                               time_period='stub_timeperiod',
                               measure=stub_measure_page,
                               position=stub_measure_page.dimensions.count(),
                               table=grouped_table())

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope='function')
def stub_page_with_single_series_bar_chart(db_session, stub_measure_page):

    db_dimension = DbDimension(guid='stub_dimension',
                               title='stub dimension',
                               time_period='stub_timeperiod',
                               measure=stub_measure_page,
                               position=stub_measure_page.dimensions.count(),
                               chart=single_series_bar_chart())

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope='function')
def stub_page_with_single_series_bar_chart(db_session, stub_measure_page):

    db_dimension = DbDimension(guid='stub_dimension',
                               title='stub dimension',
                               time_period='stub_timeperiod',
                               measure=stub_measure_page,
                               position=stub_measure_page.dimensions.count(),
                               chart=multi_series_bar_chart())

    stub_measure_page.dimensions.append(db_dimension)

    db_session.session.add(stub_measure_page)
    db_session.session.commit()
    return stub_measure_page


@pytest.fixture(scope='function')
def stub_simple_table_object():
    return simple_table()


@pytest.fixture(scope='function')
def stub_grouped_table_object():
    return grouped_table()


@pytest.fixture(scope='function')
def mock_request_build(mocker):
    return mocker.patch('application.cms.views.build_service.request_build')


@pytest.fixture(scope='function')
def mock_page_service_mark_page_published(mocker):
    return mocker.patch('application.cms.page_service.page_service.mark_page_published')


@pytest.fixture(scope='function')
def mock_send_email(mocker):
    return mocker.patch('application.admin.views._send_email')

import uuid

import pytest
from datetime import datetime
from application.cms.exceptions import PageExistsException, PageUnEditable, PageNotFoundException
from application.cms.models import Dimension, Page
from application.cms.page_service import PageService

page_service = PageService()


def test_create_page(db_session, stub_subtopic_page, test_app_editor):

    created_page = page_service.create_page('measure', stub_subtopic_page,
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()},
                                            created_by=test_app_editor.email)

    page_from_db = page_service.get_page('who_cares')

    assert page_from_db.title == created_page.title
    assert page_from_db.guid == created_page.guid
    assert page_from_db.created_by == test_app_editor.email


def test_create_page_with_guid_already_exists_raises_exception(db_session, stub_subtopic_page, test_app_editor):

    with pytest.raises(PageExistsException):
        created_page = page_service.create_page('measure',
                                                stub_subtopic_page,
                                                data={'title': 'Who cares',
                                                      'guid': 'who_cares',
                                                      'publication_date': datetime.now().date()},
                                                created_by=test_app_editor.email)  # noqa

        page_service.create_page('measure',
                                 stub_subtopic_page,
                                 data={'title': created_page.title,
                                       'guid': created_page.guid,
                                       'publication_date': created_page.publication_date},
                                 created_by=test_app_editor.email)  # noqa


def test_get_pages_by_type(stub_topic_page, stub_subtopic_page, stub_measure_page):

    pages = page_service.get_pages_by_type('topic')
    assert len(pages) == 1
    assert stub_topic_page == pages[0]

    pages = page_service.get_pages_by_type('subtopic')
    assert len(pages) == 1
    assert stub_subtopic_page == pages[0]

    pages = page_service.get_pages_by_type('measure')
    assert len(pages) == 1
    assert stub_measure_page == pages[0]


def test_get_page_by_guid(stub_measure_page):

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db == stub_measure_page


def test_get_page_by_uri(stub_subtopic_page, stub_measure_page):

    page_from_db = page_service.get_page_by_uri_and_version(stub_subtopic_page.guid,
                                                            stub_measure_page.uri,
                                                            stub_measure_page.version)
    assert page_from_db == stub_measure_page


def test_get_page_by_uri_raises_exception_if_page_does_not_exist():

    with pytest.raises(PageNotFoundException):
        page_service.get_page_by_uri_and_version('not', 'known', 'at all')


def test_get_page_by_guid_raises_exception_if_page_does_not_exist():

    with pytest.raises(PageNotFoundException):
        page_service.get_page('notthere')


def test_update_page(db_session, stub_measure_page, test_app_editor):

    page_service.update_page(stub_measure_page,
                             data={'title': 'I cares too much!',
                                   'db_version_id': stub_measure_page.db_version_id},
                             last_updated_by=test_app_editor.email)

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.title == 'I cares too much!'
    assert page_from_db.last_updated_by == test_app_editor.email


def test_update_page_raises_exception_if_page_not_editable(db_session, stub_measure_page, test_app_editor):

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'DRAFT'

    page_service.update_page(stub_measure_page,
                             data={'title': 'Who cares', 'status': 'APPROVED',
                                   'db_version_id': stub_measure_page.db_version_id},
                             last_updated_by=test_app_editor.email)

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'APPROVED'

    with pytest.raises(PageUnEditable):
        page_service.update_page(stub_measure_page,
                                 data={'title': 'I cares too much!', 'db_version_id': stub_measure_page.db_version_id},
                                 last_updated_by=test_app_editor.email)


def test_set_page_to_next_state(db_session, stub_measure_page, test_app_editor):

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'DRAFT'

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'INTERNAL_REVIEW'
    assert page_from_db.last_updated_by == test_app_editor.email

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'DEPARTMENT_REVIEW'
    assert page_from_db.last_updated_by == test_app_editor.email

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'APPROVED'
    assert page_from_db.last_updated_by == test_app_editor.email
    assert page_from_db.published_by == test_app_editor.email


def test_reject_page(db_session, stub_measure_page, test_app_editor):

    page_service.update_page(stub_measure_page,
                             data={'title': 'Who cares', 'status': 'DEPARTMENT_REVIEW',
                                   'db_version_id': stub_measure_page.db_version_id},
                             last_updated_by=test_app_editor.email)

    page_from_db = page_service.get_page(stub_measure_page.guid)

    assert page_from_db.status == 'DEPARTMENT_REVIEW'

    message = page_service.reject_page(page_from_db.guid, page_from_db.version)
    assert message == 'Sent page "Who cares" to REJECTED'

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == 'REJECTED'


def test_create_dimension_on_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    page_service.create_dimension(stub_measure_page,
                                  title='test-dimension',
                                  time_period='time_period',
                                  summary='summary',
                                  ethnicity_category='')

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid
    assert stub_measure_page.dimensions[0].title == db_dimension.title


def test_delete_dimension_from_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    page_service.create_dimension(stub_measure_page,
                                  title='test-dimension',
                                  time_period='time_period',
                                  summary='summary', ethnicity_category='')

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid

    page_service.delete_dimension(stub_measure_page, db_dimension.guid)
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0


def test_update_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = page_service.create_dimension(stub_measure_page,
                                              title='test-dimension',
                                              time_period='time_period',
                                              summary='summary', ethnicity_category='')

    update_data = {'title': 'updated-title', 'time_period': 'updated_time_period'}

    page_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.title == 'updated-title'
    assert updated_dimension.time_period == 'updated_time_period'


def test_add_chart_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = page_service.create_dimension(stub_measure_page,
                                              title='test-dimension',
                                              time_period='time_period',
                                              summary='summary', ethnicity_category='')

    chart = {"chart_is_just_a": "dictionary"}

    update_data = {'chart': chart}

    page_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.chart
    assert updated_dimension.chart == chart


def test_add_table_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = page_service.create_dimension(stub_measure_page,
                                              title='test-dimension',
                                              time_period='time_period',
                                              summary='summary', ethnicity_category='')

    table = {"table_is_just_a": "dictionary"}

    update_data = {'table': table}

    page_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.table
    assert updated_dimension.table == table


def test_delete_chart_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = page_service.create_dimension(stub_measure_page,
                                              title='test-dimension',
                                              time_period='time_period',
                                              summary='summary', ethnicity_category='')

    chart = {"chart_is_just_a": "dictionary"}
    update_data = {'chart': chart}
    page_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.chart

    page_service.delete_chart(updated_dimension)
    assert not updated_dimension.chart


def test_delete_table_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = page_service.create_dimension(stub_measure_page,
                                              title='test-dimension',
                                              time_period='time_period',
                                              summary='summary', ethnicity_category='')

    table = {"table_is_just_a": "dictionary"}
    update_data = {'table': table}
    page_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.table

    page_service.delete_table(updated_dimension)
    assert not updated_dimension.table


def test_add_or_update_dimensions_to_measure_page_preserves_order(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    d1 = page_service.create_dimension(stub_measure_page,
                                       title='test-dimension-1',
                                       time_period='time_period',
                                       summary='summary', ethnicity_category='')

    d2 = page_service.create_dimension(stub_measure_page,
                                       title='test-dimension-2',
                                       time_period='time_period',
                                       summary='summary', ethnicity_category='')

    assert stub_measure_page.dimensions[0].title == d1.title
    assert d1.position == 0
    assert stub_measure_page.dimensions[0].position == d1.position

    assert stub_measure_page.dimensions[1].title == 'test-dimension-2'
    assert d2.position == 1
    assert stub_measure_page.dimensions[1].position == d2.position

    # after update. positions should not have changed
    page_service.update_dimension(d1, {'summary': 'updated summary'})
    assert d1.summary == 'updated summary'
    assert d1.position == 0
    assert d2.position == 1


def test_create_page_with_uri_already_exists_under_subtopic_raises_exception(db_session,
                                                                             stub_subtopic_page,
                                                                             test_app_editor):

    existing_page = page_service.create_page('measure',
                                             stub_subtopic_page, data={'title': 'Who cares',
                                                                       'guid': 'who_cares',
                                                                       'publication_date': datetime.now().date()},
                                             created_by=test_app_editor.email)

    with pytest.raises(PageExistsException):
        page_service.create_page('measure', stub_subtopic_page, data={'title': existing_page.title,
                                                                      'guid': 'who_cares but does not clash',
                                                                      'publication_date': datetime.now().date()},
                                 created_by=test_app_editor.email)


def test_page_can_be_created_if_uri_unique(db_session, stub_subtopic_page):
    can_not_be_created, message = page_service.page_cannot_be_created(stub_subtopic_page.guid, 'also-unique')

    assert can_not_be_created is False
    assert 'Page with parent subtopic_example and uri also-unique does not exist' == message


def test_page_can_be_created_if_subtopic_and_uri_unique(db_session, stub_measure_page):

    non_clashing_uri = '%s-%s' % (stub_measure_page.uri, 'something-new')

    can_not_be_created, message = page_service.page_cannot_be_created(stub_measure_page.parent_guid,
                                                                      non_clashing_uri)

    assert can_not_be_created is False
    assert 'Page with parent subtopic_example and uri test-measure-page-something-new does not exist' == message


def test_page_cannot_be_created_if_uri_is_not_unique_for_subtopic(db_session, stub_measure_page):

    can_not_be_created, message = page_service.page_cannot_be_created(stub_measure_page.parent_guid,
                                                                      stub_measure_page.uri)

    assert can_not_be_created is True
    assert message == 'Page title "%s" and uri "%s" already exists under "subtopic_example"' % (stub_measure_page.title,
                                                                                                stub_measure_page.uri)


def test_get_latest_publishable_versions_of_measures_for_subtopic(db, db_session, stub_subtopic_page):

    major_version_1 = Page(guid='test_page', version='1.0', status='APPROVED')
    minor_version_2 = Page(guid='test_page', version='1.1', status='APPROVED')
    minor_version_3 = Page(guid='test_page', version='1.2', status='APPROVED')
    minor_version_4 = Page(guid='test_page', version='1.3', status='DRAFT')

    stub_subtopic_page.children.append(major_version_1)
    stub_subtopic_page.children.append(minor_version_2)
    stub_subtopic_page.children.append(minor_version_3)
    stub_subtopic_page.children.append(minor_version_4)

    db.session.add(stub_subtopic_page)
    db.session.add(minor_version_2)
    db.session.add(minor_version_3)
    db.session.add(minor_version_4)

    db.session.commit()

    measures = page_service.get_latest_publishable_measures(stub_subtopic_page, ['APPROVED'])
    assert len(measures) == 1


def test_create_new_version_of_page(db, db_session, stub_measure_page):

    new_version = page_service.create_copy(stub_measure_page.guid, stub_measure_page.version, 'minor')

    assert new_version.version == '1.1'
    assert new_version.status == 'DRAFT'
    assert new_version.internal_edit_summary is None
    assert new_version.external_edit_summary is None
    assert new_version.publication_date is None
    assert not new_version.published

    new_version = page_service.create_copy(stub_measure_page.guid, stub_measure_page.version, 'major')

    assert new_version.version == '2.0'
    assert new_version.status == 'DRAFT'
    assert new_version.internal_edit_summary is None
    assert new_version.external_edit_summary is None
    assert new_version.publication_date is None
    assert not new_version.published


def test_create_page_trims_whitespace(db_session, stub_subtopic_page, test_app_editor):
    page = page_service.create_page('measure',
                                    stub_subtopic_page,
                                    data={'title': '\n\t   Who cares\n',
                                          'publication_date': datetime.now().date(),
                                          'source_text': '\n\n\n\n\n\n'},
                                    created_by=test_app_editor.email)

    assert page.title == 'Who cares'
    assert page.source_text is None


def test_update_page_trims_whitespace(db_session, stub_measure_page, test_app_editor):
    page = page_service.update_page(stub_measure_page, data={'title': 'Who cares',
                                                             'db_version_id': stub_measure_page.db_version_id,
                                                             'publication_date': datetime.now().date(),
                                                             'ethnicity_definition_summary':
                                                                 '\n\n\n\n\n\nThis is what should be left\n'},
                                    last_updated_by=test_app_editor.email)

    assert page.ethnicity_definition_summary == 'This is what should be left'

    page_service.update_page(stub_measure_page,
                             data={'title': 'Who cares',
                                   'ethnicity_definition_summary':
                                       '\n   How about some more whitespace? \n             \n',
                                   'db_version_id': stub_measure_page.db_version_id},
                             last_updated_by=test_app_editor.email)

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.ethnicity_definition_summary == 'How about some more whitespace?'

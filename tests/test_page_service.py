import pytest
from datetime import datetime
from application.cms.exceptions import PageExistsException, PageUnEditable
from application.cms.page_service import PageService

page_service = PageService()


def test_create_page(db_session):

    created_page = page_service.create_page('measure',
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()})

    page_from_db = page_service.get_page('who_cares')

    assert page_from_db.title == created_page.title
    assert page_from_db.guid == created_page.guid


def test_create_page_with_guid_already_exists_raises_exception(db_session):

    with pytest.raises(PageExistsException):
        created_page = page_service.create_page('measure', data={'title': 'Who cares',
                                                                 'guid': 'who_cares',
                                                                 'publication_date': datetime.now().date()})

        page_service.create_page('measure', data={'title': created_page.title,
                                                  'guid': created_page.guid,
                                                  'publication_date': created_page.publication_date})


def test_get_topics(stub_topic_page):

    topics = page_service.get_topics()
    assert len(topics) == 1
    assert stub_topic_page.guid == topics[0].guid


def test_get_pages(stub_topic_page, stub_subtopic_page, stub_measure_page):

    pages = page_service.get_pages()
    assert len(pages) == 3
    assert stub_topic_page in pages
    assert stub_subtopic_page in pages
    assert stub_measure_page in pages


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

    page_from_db = page_service.get_page_by_uri(stub_subtopic_page.guid, stub_measure_page.uri)
    assert page_from_db == stub_measure_page


def test_get_page_by_uri_returns_none_if_page_does_not_exist():

    page = page_service.get_page_by_uri('not', 'known')
    assert page is None


def test_get_page_by_guid_returns_none_if_page_does_not_exist():

    page = page_service.get_page('notthere')
    assert page is None


def test_update_page(db_session):

    created_page = page_service.create_page('measure',
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()})

    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.guid == created_page.guid

    page_service.update_page(created_page, data={'title': 'I cares too much!'})

    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.title == 'I cares too much!'


def test_update_page_raises_exception_if_page_not_editable(db_session):

    created_page = page_service.create_page('measure',
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()})

    page_from_db = page_service.get_page('who_cares')
    assert page_from_db.status == 'DRAFT'

    page_service.update_page(created_page, data={'status': 'ACCEPTED'})
    page_from_db = page_service.get_page('who_cares')
    assert page_from_db.status == 'ACCEPTED'

    with pytest.raises(PageUnEditable):
        page_service.update_page(created_page, data={'title': 'I cares too much!'})


def test_set_page_to_next_state(db_session):

    created_page = page_service.create_page('measure',
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()})

    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.status == 'DRAFT'

    page_service.next_state(page_from_db)
    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.status == 'INTERNAL_REVIEW'

    page_service.next_state(page_from_db)
    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.status == 'DEPARTMENT_REVIEW'

    page_service.next_state(page_from_db)
    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.status == 'ACCEPTED'


def test_reject_page(db_session):
    created_page = page_service.create_page('measure',
                                            data={'title': 'Who cares',
                                                  'guid': 'who_cares',
                                                  'publication_date': datetime.now().date()})

    page_service.update_page(created_page, data={'status': 'DEPARTMENT_REVIEW'})
    page_from_db = page_service.get_page(created_page.guid)

    assert page_from_db.status == 'DEPARTMENT_REVIEW'

    message = page_service.reject_page(page_from_db)
    assert message == 'updating page "Who cares" state from "DEPARTMENT_REVIEW" to "REJECTED"'

    page_from_db = page_service.get_page(created_page.guid)
    assert page_from_db.status == 'REJECTED'

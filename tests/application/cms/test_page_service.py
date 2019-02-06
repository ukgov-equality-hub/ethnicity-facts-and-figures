import pytest

from application.cms.exceptions import PageNotFoundException
from application.cms.page_service import PageService

page_service = PageService()


def test_get_pages_by_type(stub_topic_page, stub_subtopic_page, stub_measure_page):
    pages = page_service.get_pages_by_type("topic")
    assert len(pages) == 1
    assert stub_topic_page == pages[0]

    pages = page_service.get_pages_by_type("subtopic")
    assert len(pages) == 1
    assert stub_subtopic_page == pages[0]

    pages = page_service.get_pages_by_type("measure")
    assert len(pages) == 1
    assert stub_measure_page == pages[0]


def test_get_page_by_guid(stub_measure_page):
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db == stub_measure_page


def test_get_page_by_guid_raises_exception_if_page_does_not_exist():
    with pytest.raises(PageNotFoundException):
        page_service.get_page("notthere")

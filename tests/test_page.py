import pytest

from application.cms.exceptions import RejectionImpossible


def test_publish_to_internal_review(stub_topic_page):
    assert stub_topic_page.meta.status == 'DRAFT'
    stub_topic_page.next_state()
    assert stub_topic_page.meta.status == 'INTERNAL_REVIEW'


def test_publish_to_department_review(stub_topic_page):
    assert stub_topic_page.meta.status == 'DRAFT'
    stub_topic_page.meta.status = 'INTERNAL_REVIEW'
    stub_topic_page.next_state()
    assert stub_topic_page.meta.status == 'DEPARTMENT_REVIEW'


def test_publish_to_accepted(stub_topic_page):
    assert stub_topic_page.meta.status == 'DRAFT'
    stub_topic_page.meta.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.next_state()
    assert stub_topic_page.meta.status == 'ACCEPTED'


def test_reject_in_internal_review(stub_topic_page):
    stub_topic_page.meta.status = 'INTERNAL_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.meta.status == 'REJECTED'


def test_reject_in_department_review(stub_topic_page):
    stub_topic_page.meta.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.meta.status == 'REJECTED'


def test_cannot_reject_accepted_page(stub_topic_page):
    stub_topic_page.meta.status = 'ACCEPTED'
    with pytest.raises(RejectionImpossible):
        stub_topic_page.reject()

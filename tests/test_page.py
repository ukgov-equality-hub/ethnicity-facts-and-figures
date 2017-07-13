import pytest

from datetime import datetime, timedelta
from application.cms.exceptions import RejectionImpossible


def test_publish_to_internal_review(stub_topic_page):
    assert stub_topic_page.status == 'DRAFT'
    stub_topic_page.next_state()
    assert stub_topic_page.status == 'INTERNAL_REVIEW'


def test_publish_to_department_review(stub_topic_page):
    assert stub_topic_page.status == 'DRAFT'
    stub_topic_page.status = 'INTERNAL_REVIEW'
    stub_topic_page.next_state()
    assert stub_topic_page.status == 'DEPARTMENT_REVIEW'


def test_publish_to_approved(stub_topic_page):
    assert stub_topic_page.status == 'DRAFT'
    stub_topic_page.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.next_state()
    assert stub_topic_page.status == 'APPROVED'


def test_reject_in_internal_review(stub_topic_page):
    stub_topic_page.status = 'INTERNAL_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.status == 'REJECTED'


def test_reject_in_department_review(stub_topic_page):
    stub_topic_page.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.status == 'REJECTED'


def test_cannot_reject_approved_page(stub_topic_page):
    stub_topic_page.status = 'APPROVED'
    with pytest.raises(RejectionImpossible):
        stub_topic_page.reject()


def test_page_with_no_publication_date_should_be_published_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'APPROVED'

    assert stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_in_future_should_be_not_be_published_even_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'APPROVED'

    tomorrow = datetime.now() + timedelta(days=1)
    stub_measure_page.publication_date = tomorrow.date()

    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_in_past_should_be_published_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'APPROVED'

    yesterday = datetime.now() - timedelta(days=1)
    stub_measure_page.publication_date = yesterday.date()

    assert stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_in_past_should_be_not_be_published_if_not_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    yesterday = datetime.now() - timedelta(days=1)
    stub_measure_page.publication_date = yesterday.date()

    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_of_today_should_be_not_be_published_if_not_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    stub_measure_page.publication_date = datetime.now().date()

    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_of_today_should_be_published_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'APPROVED'

    stub_measure_page.publication_date = datetime.now().date()

    assert stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_available_actions_for_page_in_draft(stub_measure_page):

    expected_available_actions = ['UPDATE', 'APPROVE']

    assert stub_measure_page.status == 'DRAFT'
    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_page_in_internal_review(stub_measure_page):

    expected_available_actions = ['APPROVE', 'REJECT']

    stub_measure_page.status = 'INTERNAL_REVIEW'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_page_in_department_review(stub_measure_page):

    expected_available_actions = ['APPROVE', 'REJECT']

    stub_measure_page.status = 'DEPARTMENT_REVIEW'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_rejected_page(stub_measure_page):

    expected_available_actions = ['UPDATE']

    stub_measure_page.reject()
    assert stub_measure_page.status == 'REJECTED'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_approved_page(stub_measure_page):

    expected_available_actions = ['UNPUBLISH']

    stub_measure_page.status = 'APPROVED'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_unpublish_page(stub_topic_page):
    stub_topic_page.status = 'APPROVED'
    stub_topic_page.unpublish()
    assert stub_topic_page.status == 'UNPUBLISHED'

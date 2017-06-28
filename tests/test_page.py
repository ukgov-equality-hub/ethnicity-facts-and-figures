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


def test_publish_to_accepted(stub_topic_page):
    assert stub_topic_page.status == 'DRAFT'
    stub_topic_page.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.next_state()
    assert stub_topic_page.status == 'ACCEPTED'


def test_reject_in_internal_review(stub_topic_page):
    stub_topic_page.status = 'INTERNAL_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.status == 'REJECTED'


def test_reject_in_department_review(stub_topic_page):
    stub_topic_page.status = 'DEPARTMENT_REVIEW'
    stub_topic_page.reject()
    assert stub_topic_page.status == 'REJECTED'


def test_cannot_reject_accepted_page(stub_topic_page):
    stub_topic_page.status = 'ACCEPTED'
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
    assert stub_measure_page.status == 'ACCEPTED'

    assert stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)


def test_page_with_publication_date_in_future_should_be_not_be_published_even_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'ACCEPTED'

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
    assert stub_measure_page.status == 'ACCEPTED'

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
    assert stub_measure_page.status == 'ACCEPTED'

    stub_measure_page.publication_date = datetime.now().date()

    assert stub_measure_page.eligible_for_build(Config.BETA_PUBLICATION_STATES)

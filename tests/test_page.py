import pytest

from datetime import datetime, timedelta
from application.cms.exceptions import RejectionImpossible
from application.cms.models import DbPage


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


def test_page_should_be_published_if_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.PUBLICATION_STATES)

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == 'APPROVED'

    assert stub_measure_page.eligible_for_build(Config.PUBLICATION_STATES)


def test_page_should_not_be_published_if_not_in_right_state(stub_measure_page):

    from application.config import Config

    assert stub_measure_page.status == 'DRAFT'
    assert not stub_measure_page.eligible_for_build(Config.PUBLICATION_STATES)

    assert not stub_measure_page.eligible_for_build(Config.PUBLICATION_STATES)


def test_available_actions_for_page_in_draft(stub_measure_page):

    expected_available_actions = ['APPROVE', 'UPDATE']

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

    expected_available_actions = ['RETURN_TO_DRAFT']

    stub_measure_page.reject()
    assert stub_measure_page.status == 'REJECTED'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_approved_page(stub_measure_page):

    expected_available_actions = ['UNPUBLISH']

    stub_measure_page.status = 'APPROVED'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_no_available_actions_for_page_awaiting_unpublication(stub_measure_page):

    expected_available_actions = []

    stub_measure_page.status = 'UNPUBLISH'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_unpublished(stub_measure_page):

    expected_available_actions = ['RETURN_TO_DRAFT']

    stub_measure_page.status = 'UNPUBLISHED'

    assert expected_available_actions == stub_measure_page.available_actions()


def test_unpublish_page(stub_topic_page):
    stub_topic_page.status = 'APPROVED'
    stub_topic_page.unpublish()
    assert stub_topic_page.status == 'UNPUBLISH'


def test_page_sort_by_version():

    first_page = DbPage(guid='test_page', version='1.0')
    second_page = DbPage(guid='test_page', version='1.1')
    third_page = DbPage(guid='test_page', version='2.0')
    fourth_page = DbPage(guid='test_page', version='2.2')
    fifth_page = DbPage(guid='test_page', version='2.10')
    sixth_page = DbPage(guid='test_page', version='2.20')

    pages = [fourth_page, sixth_page, fifth_page, second_page, first_page, third_page]

    pages.sort()

    assert pages[0] == first_page
    assert pages[1] == second_page
    assert pages[2] == third_page
    assert pages[3] == fourth_page
    assert pages[4] == fifth_page
    assert pages[5] == sixth_page


def test_page_has_minor_update(db, db_session):
    major_version = DbPage(guid='test_page', version='1.0')
    minor_version = DbPage(guid='test_page', version='1.1')

    db.session.add(major_version)
    db.session.add(minor_version)

    db.session.commit()

    major_version.has_minor_update()


def test_page_has_major_update(db, db_session):
    major_version_1 = DbPage(guid='test_page', version='1.0')
    major_version_2 = DbPage(guid='test_page', version='2.0')

    db.session.add(major_version_1)
    db.session.add(major_version_2)

    db.session.commit()

    major_version_1.has_major_update()


def test_page_is_latest(db, db_session):
    major_version_1 = DbPage(guid='test_page', version='1.0')
    minor_version = DbPage(guid='test_page', version='1.1')
    major_version_2 = DbPage(guid='test_page', version='2.0')

    db.session.add(major_version_1)
    db.session.add(minor_version)
    db.session.add(major_version_2)
    db.session.commit()

    assert major_version_1.is_latest() is False
    assert minor_version.is_latest() is False
    assert major_version_2.is_latest() is True


def test_page_has_correct_number_of_versions(db, db_session):

    major_version_1 = DbPage(guid='test_page', version='1.0')
    minor_version = DbPage(guid='test_page', version='1.1')
    major_version_2 = DbPage(guid='test_page', version='2.0')

    db.session.add(major_version_1)
    db.session.add(minor_version)
    db.session.add(major_version_2)
    db.session.commit()

    assert major_version_1.number_of_versions() == 3
    assert minor_version.number_of_versions() == 3
    assert major_version_2.number_of_versions() == 3


def test_page_has_later_published_versions(db, db_session):

    major_version_1 = DbPage(guid='test_page', version='1.0', status='APPROVED')
    minor_version_2 = DbPage(guid='test_page', version='1.1', status='APPROVED')
    minor_version_3 = DbPage(guid='test_page', version='1.2', status='APPROVED')
    minor_version_4 = DbPage(guid='test_page', version='1.3', status='DRAFT')

    db.session.add(major_version_1)
    db.session.add(minor_version_2)
    db.session.add(minor_version_3)
    db.session.add(minor_version_4)
    db.session.commit()

    assert major_version_1.has_no_later_published_versions(['APPROVED']) is False
    assert minor_version_2.has_no_later_published_versions(['APPROVED']) is False
    assert minor_version_3.has_no_later_published_versions(['APPROVED']) is True
    assert minor_version_4.has_no_later_published_versions(['APPROVED']) is True


def test_get_latest_version_of_page(db, db_session):
    version_1 = DbPage(guid='test_page', version='1.0')
    version_2 = DbPage(guid='test_page', version='1.1')
    version_3 = DbPage(guid='test_page', version='2.0')
    version_4 = DbPage(guid='test_page', version='2.1')

    db.session.add(version_1)
    db.session.add(version_2)
    db.session.add(version_3)
    db.session.add(version_4)
    db.session.commit()

    assert version_1.is_latest() is False
    assert version_2.is_latest() is False
    assert version_3.is_latest() is False
    assert version_4.is_latest() is True


def test_is_minor_or_minor_version():
    page = DbPage(guid='test_page', version='1.0')

    assert page.version == '1.0'
    assert page.is_major_version() is True
    assert page.is_minor_version() is False

    page.version = page.next_minor_version()

    assert page.version == '1.1'
    assert page.is_major_version() is False
    assert page.is_minor_version() is True

    page.version = page.next_major_version()

    assert page.version == '2.0'
    assert page.is_major_version() is True
    assert page.is_minor_version() is False

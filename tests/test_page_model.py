import pytest

from application.cms.exceptions import RejectionImpossible
from application.cms.models import MeasureVersion, UKCountry

from tests.utils import create_measure_page_versions


def test_publish_to_internal_review(stub_topic_page):
    assert stub_topic_page.status == "DRAFT"
    stub_topic_page.next_state()
    assert stub_topic_page.status == "INTERNAL_REVIEW"


def test_publish_to_department_review(stub_topic_page):
    assert stub_topic_page.status == "DRAFT"
    stub_topic_page.status = "INTERNAL_REVIEW"
    stub_topic_page.next_state()
    assert stub_topic_page.status == "DEPARTMENT_REVIEW"


def test_publish_to_approved(stub_topic_page):
    assert stub_topic_page.status == "DRAFT"
    stub_topic_page.status = "DEPARTMENT_REVIEW"
    stub_topic_page.next_state()
    assert stub_topic_page.status == "APPROVED"


def test_reject_in_internal_review(stub_topic_page):
    stub_topic_page.status = "INTERNAL_REVIEW"
    stub_topic_page.reject()
    assert stub_topic_page.status == "REJECTED"


def test_reject_in_department_review(stub_topic_page):
    stub_topic_page.status = "DEPARTMENT_REVIEW"
    stub_topic_page.reject()
    assert stub_topic_page.status == "REJECTED"


def test_cannot_reject_approved_page(stub_topic_page):
    stub_topic_page.status = "APPROVED"
    with pytest.raises(RejectionImpossible):
        stub_topic_page.reject()


def test_page_should_be_published_if_in_right_state(stub_measure_page):

    assert stub_measure_page.status == "DRAFT"
    assert not stub_measure_page.eligible_for_build()

    # move page to accepted state
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    stub_measure_page.next_state()
    assert stub_measure_page.status == "APPROVED"

    assert stub_measure_page.eligible_for_build()


def test_page_should_not_be_published_if_not_in_right_state(stub_measure_page):

    assert stub_measure_page.status == "DRAFT"

    assert not stub_measure_page.eligible_for_build()


def test_available_actions_for_page_in_draft(stub_measure_page):

    expected_available_actions = ["APPROVE", "UPDATE"]

    assert stub_measure_page.status == "DRAFT"
    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_page_in_internal_review(stub_measure_page):

    expected_available_actions = ["APPROVE", "REJECT"]

    stub_measure_page.status = "INTERNAL_REVIEW"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_page_in_department_review(stub_measure_page):

    expected_available_actions = ["APPROVE", "REJECT"]

    stub_measure_page.status = "DEPARTMENT_REVIEW"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_rejected_page(stub_measure_page):

    expected_available_actions = ["RETURN_TO_DRAFT"]

    stub_measure_page.reject()
    assert stub_measure_page.status == "REJECTED"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_approved_page(stub_measure_page):

    expected_available_actions = ["UNPUBLISH"]

    stub_measure_page.status = "APPROVED"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_no_available_actions_for_page_awaiting_unpublication(stub_measure_page):

    expected_available_actions = []

    stub_measure_page.status = "UNPUBLISH"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_available_actions_for_unpublished(stub_measure_page):

    expected_available_actions = ["RETURN_TO_DRAFT"]

    stub_measure_page.status = "UNPUBLISHED"

    assert expected_available_actions == stub_measure_page.available_actions()


def test_unpublish_page(stub_topic_page):
    stub_topic_page.status = "APPROVED"
    stub_topic_page.unpublish()
    assert stub_topic_page.status == "UNPUBLISH"


def test_page_sort_by_version():

    first_page = MeasureVersion(guid="test_page", version="1.0")
    second_page = MeasureVersion(guid="test_page", version="1.1")
    third_page = MeasureVersion(guid="test_page", version="2.0")
    fourth_page = MeasureVersion(guid="test_page", version="2.2")
    fifth_page = MeasureVersion(guid="test_page", version="2.10")
    sixth_page = MeasureVersion(guid="test_page", version="2.20")

    pages = [fourth_page, sixth_page, fifth_page, second_page, first_page, third_page]

    pages.sort()

    assert pages[0] == first_page
    assert pages[1] == second_page
    assert pages[2] == third_page
    assert pages[3] == fourth_page
    assert pages[4] == fifth_page
    assert pages[5] == sixth_page


def test_page_has_minor_update(db, db_session):
    major_version = MeasureVersion(guid="test_page", version="1.0")
    minor_version = MeasureVersion(guid="test_page", version="1.1")

    db.session.add(major_version)
    db.session.add(minor_version)

    db.session.commit()

    major_version.has_minor_update()


def test_page_has_major_update(db, db_session):
    major_version_1 = MeasureVersion(guid="test_page", version="1.0")
    major_version_2 = MeasureVersion(guid="test_page", version="2.0")

    db.session.add(major_version_1)
    db.session.add(major_version_2)

    db.session.commit()

    major_version_1.has_major_update()


def test_page_has_correct_number_of_versions(db, db_session):

    major_version_1 = MeasureVersion(guid="test_page", version="1.0")
    minor_version = MeasureVersion(guid="test_page", version="1.1")
    major_version_2 = MeasureVersion(guid="test_page", version="2.0")

    db.session.add(major_version_1)
    db.session.add(minor_version)
    db.session.add(major_version_2)
    db.session.commit()

    assert major_version_1.number_of_versions() == 3
    assert minor_version.number_of_versions() == 3
    assert major_version_2.number_of_versions() == 3


def test_page_has_later_published_versions(db, db_session):

    major_version_1 = MeasureVersion(guid="test_page", version="1.0", status="APPROVED")
    minor_version_2 = MeasureVersion(guid="test_page", version="1.1", status="APPROVED")
    minor_version_3 = MeasureVersion(guid="test_page", version="1.2", status="APPROVED")
    minor_version_4 = MeasureVersion(guid="test_page", version="1.3", status="DRAFT")

    db.session.add(major_version_1)
    db.session.add(minor_version_2)
    db.session.add(minor_version_3)
    db.session.add(minor_version_4)
    db.session.commit()

    assert major_version_1.has_no_later_published_versions() is False
    assert minor_version_2.has_no_later_published_versions() is False
    assert minor_version_3.has_no_later_published_versions() is True
    assert minor_version_4.has_no_later_published_versions() is True


def test_is_minor_or_minor_version():
    page = MeasureVersion(guid="test_page", version="1.0")

    assert page.version == "1.0"
    assert page.is_major_version() is True
    assert page.is_minor_version() is False

    page.version = page.next_minor_version()

    assert page.version == "1.1"
    assert page.is_major_version() is False
    assert page.is_minor_version() is True

    page.version = page.next_major_version()

    assert page.version == "2.0"
    assert page.is_major_version() is True
    assert page.is_minor_version() is False


@pytest.mark.parametrize(
    "page_versions, expected_order",
    (
        (["1.0", "1.1", "1.2", "2.0"], ["2.0", "1.2", "1.1", "1.0"]),
        (["2.0", "1.2", "1.1", "1.0"], ["2.0", "1.2", "1.1", "1.0"]),
        (["2.0", "4.1", "3.0", "8.2", "1.0"], ["8.2", "4.1", "3.0", "2.0", "1.0"]),
    ),
)
def test_get_measure_page_versions_returns_pages_ordered_by_version(
    db_session, page_service, stub_measure_page, page_versions, expected_order
):
    create_measure_page_versions(db_session, stub_measure_page, page_versions)

    assert [
        page.version
        for page in page_service.get_measure_page_versions(
            parent_guid=stub_measure_page.parent.guid, measure_slug="test-measure-page-2"
        )
    ] == expected_order


@pytest.mark.parametrize(
    "page_versions, expected_version",
    (
        (["1.0", "1.1", "1.2", "2.0"], "2.0"),
        (["2.0", "1.2", "1.1", "1.0"], "2.0"),
        (["2.0", "4.1", "3.0", "8.2", "1.0"], "8.2"),
    ),
)
def test_get_latest_version_returns_latest_measure_page(
    db_session, page_service, stub_measure_page, page_versions, expected_version
):
    create_measure_page_versions(db_session, stub_measure_page, page_versions)

    assert (
        page_service.get_latest_version(
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug="test-measure-page-2",
        ).version
        == expected_version
    )


@pytest.mark.parametrize(
    "page_versions, page_titles, expected_version_order, expected_title_order",
    (
        (["1.0", "2.0"], ["Test", "Test"], ["2.0", "1.0"], ["Test", "Test"]),
        (["2.0", "1.0"], ["Test", "Test"], ["2.0", "1.0"], ["Test", "Test"]),
        (["1.0", "2.0"], ["Test 1", "Test 2"], ["1.0", "2.0"], ["Test 1", "Test 2"]),
        (["2.0", "1.0"], ["Test 1", "Test 2"], ["2.0", "1.0"], ["Test 1", "Test 2"]),
        (
            ["2.0", "1.0", "3.0", "1.1"],
            ["Test", "Test", "Test", "Test"],
            ["3.0", "2.0", "1.1", "1.0"],
            ["Test", "Test", "Test", "Test"],
        ),
        (
            ["2.0", "1.0", "3.0", "1.1"],
            ["Test 1", "Test 3", "Test 2", "Test 2"],
            ["2.0", "3.0", "1.1", "1.0"],
            ["Test 1", "Test 2", "Test 2", "Test 3"],
        ),
    ),
)
def test_get_pages_by_type_returns_pages_ordered_by_title_and_version(
    db_session,
    page_service,
    stub_measure_page,
    page_versions,
    page_titles,
    expected_version_order,
    expected_title_order,
):
    create_measure_page_versions(db_session, stub_measure_page, page_versions, page_titles)
    db_session.session.delete(stub_measure_page)
    db_session.session.commit()

    pages = page_service.get_pages_by_type("measure")

    assert [page.title for page in pages] == expected_title_order
    assert [page.version for page in pages] == expected_version_order


@pytest.mark.parametrize(
    "page_versions, expected_order",
    (
        (["1.0", "1.1", "1.2", "2.0"], ["2.0", "1.2", "1.1", "1.0"]),
        (["2.0", "1.2", "1.1", "1.0"], ["2.0", "1.2", "1.1", "1.0"]),
        (["2.0", "4.1", "3.0", "8.2", "1.0"], ["8.2", "4.1", "3.0", "2.0", "1.0"]),
    ),
)
def test_get_pages_by_slug_returns_pages_ordered_by_version(
    db_session, page_service, stub_measure_page, page_versions, expected_order
):
    create_measure_page_versions(db_session, stub_measure_page, page_versions)

    pages = page_service.get_pages_by_slug(stub_measure_page.parent.guid, "test-measure-page-2")
    assert [page.version for page in pages] == expected_order


@pytest.mark.parametrize(
    "countries, formatted_string",
    (
        ([UKCountry.ENGLAND], "England"),
        ([UKCountry.ENGLAND, UKCountry.WALES], "England and Wales"),
        ([UKCountry.ENGLAND, UKCountry.WALES, UKCountry.SCOTLAND, UKCountry.NORTHERN_IRELAND], "United Kingdom"),
    ),
)
def test_area_covered_formatter(countries, formatted_string):
    page = MeasureVersion(guid="test_page", version="1.0", area_covered=countries)

    assert page.format_area_covered() == formatted_string

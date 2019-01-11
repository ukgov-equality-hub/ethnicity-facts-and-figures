import pytest
from datetime import datetime
from application.cms.exceptions import PageUnEditable, PageNotFoundException
from application.cms.models import MeasureVersion
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


def test_update_page(db_session, stub_measure_page, test_app_editor):
    page_service.update_page(
        stub_measure_page,
        data={"title": "I cares too much!", "db_version_id": stub_measure_page.db_version_id},
        last_updated_by=test_app_editor.email,
        data_source_forms=[],
    )

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.title == "I cares too much!"
    assert page_from_db.last_updated_by == test_app_editor.email


def test_update_page_raises_exception_if_page_not_editable(db_session, stub_measure_page, test_app_editor):
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "DRAFT"

    page_service.update_page(
        stub_measure_page,
        data={"title": "Who cares", "status": "APPROVED", "db_version_id": stub_measure_page.db_version_id},
        last_updated_by=test_app_editor.email,
        data_source_forms=[],
    )

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "APPROVED"

    with pytest.raises(PageUnEditable):
        page_service.update_page(
            stub_measure_page,
            data={"title": "I cares too much!", "db_version_id": stub_measure_page.db_version_id},
            last_updated_by=test_app_editor.email,
            data_source_forms=[],
        )


def test_set_page_to_next_state(db_session, stub_measure_page, test_app_editor):
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "DRAFT"

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "INTERNAL_REVIEW"
    assert page_from_db.last_updated_by == test_app_editor.email

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "DEPARTMENT_REVIEW"
    assert page_from_db.last_updated_by == test_app_editor.email

    page_service.next_state(page_from_db, updated_by=test_app_editor.email)
    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "APPROVED"
    assert page_from_db.last_updated_by == test_app_editor.email
    assert page_from_db.published_by == test_app_editor.email


def test_reject_page(db_session, stub_measure_page, test_app_editor):
    page_service.update_page(
        stub_measure_page,
        data={"title": "Who cares", "status": "DEPARTMENT_REVIEW", "db_version_id": stub_measure_page.db_version_id},
        last_updated_by=test_app_editor.email,
        data_source_forms=[],
    )

    page_from_db = page_service.get_page(stub_measure_page.guid)

    assert page_from_db.status == "DEPARTMENT_REVIEW"

    message = page_service.reject_page(page_from_db.guid, page_from_db.version)
    assert message == 'Sent page "Who cares" to REJECTED'

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.status == "REJECTED"


def test_get_latest_publishable_versions_of_measures_for_subtopic(db, db_session, stub_subtopic_page, stub_measure_1):
    major_version_1 = MeasureVersion(guid="test_page", version="1.0", status="APPROVED", measure_id=stub_measure_1.id)
    minor_version_2 = MeasureVersion(guid="test_page", version="1.1", status="APPROVED", measure_id=stub_measure_1.id)
    minor_version_3 = MeasureVersion(guid="test_page", version="1.2", status="APPROVED", measure_id=stub_measure_1.id)
    minor_version_4 = MeasureVersion(guid="test_page", version="1.3", status="DRAFT", measure_id=stub_measure_1.id)

    stub_subtopic_page.children.append(major_version_1)
    stub_subtopic_page.children.append(minor_version_2)
    stub_subtopic_page.children.append(minor_version_3)
    stub_subtopic_page.children.append(minor_version_4)

    db.session.add(stub_subtopic_page)
    db.session.add(minor_version_2)
    db.session.add(minor_version_3)
    db.session.add(minor_version_4)

    db.session.commit()

    measures = page_service.get_latest_publishable_measures(stub_subtopic_page)
    assert len(measures) == 1


def test_update_page_trims_whitespace(db_session, stub_measure_page, test_app_editor):
    page = page_service.update_page(
        stub_measure_page,
        data={
            "title": "Who cares",
            "db_version_id": stub_measure_page.db_version_id,
            "published_at": datetime.now().date(),
            "ethnicity_definition_summary": "\n\n\n\n\n\nThis is what should be left\n",
        },
        last_updated_by=test_app_editor.email,
        data_source_forms=[],
    )

    assert page.ethnicity_definition_summary == "This is what should be left"

    page_service.update_page(
        stub_measure_page,
        data={
            "title": "Who cares",
            "ethnicity_definition_summary": "\n   How about some more whitespace? \n             \n",
            "db_version_id": stub_measure_page.db_version_id,
        },
        last_updated_by=test_app_editor.email,
        data_source_forms=[],
    )

    page_from_db = page_service.get_page(stub_measure_page.guid)
    assert page_from_db.ethnicity_definition_summary == "How about some more whitespace?"

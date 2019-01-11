import pytest
from datetime import datetime
from application.cms.exceptions import PageUnEditable, PageNotFoundException
from application.cms.models import MeasureVersion, DimensionClassification
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


def test_page_can_be_created_if_slug_unique(db_session, stub_subtopic_page):
    can_not_be_created, message = page_service.page_cannot_be_created(stub_subtopic_page.guid, "also-unique")

    assert can_not_be_created is False
    assert "Page with parent subtopic_example and slug also-unique does not exist" == message


def test_page_can_be_created_if_subtopic_and_slug_unique(db_session, stub_measure_page):
    non_clashing_slug = "%s-%s" % (stub_measure_page.slug, "something-new")

    can_not_be_created, message = page_service.page_cannot_be_created(stub_measure_page.parent_guid, non_clashing_slug)

    assert can_not_be_created is False
    assert "Page with parent subtopic_example and slug test-measure-page-something-new does not exist" == message


def test_page_cannot_be_created_if_slug_is_not_unique_for_subtopic(db_session, stub_measure_page):
    can_not_be_created, message = page_service.page_cannot_be_created(
        stub_measure_page.parent_guid, stub_measure_page.slug
    )

    assert can_not_be_created is True
    assert message == 'Page title "%s" and slug "%s" already exists under "subtopic_example"' % (
        stub_measure_page.title,
        stub_measure_page.slug,
    )


def test_get_latest_publishable_versions_of_measures_for_subtopic(db, db_session, stub_subtopic_page):
    major_version_1 = MeasureVersion(guid="test_page", version="1.0", status="APPROVED")
    minor_version_2 = MeasureVersion(guid="test_page", version="1.1", status="APPROVED")
    minor_version_3 = MeasureVersion(guid="test_page", version="1.2", status="APPROVED")
    minor_version_4 = MeasureVersion(guid="test_page", version="1.3", status="DRAFT")

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


def test_create_new_version_of_page(db, db_session, stub_measure_page, mock_rdu_user):
    assert stub_measure_page.latest

    new_version = page_service.create_copy(
        stub_measure_page.guid, stub_measure_page.version, "minor", mock_rdu_user.email
    )

    assert new_version.version == "1.1"
    assert new_version.status == "DRAFT"
    assert new_version.internal_edit_summary is None
    assert new_version.external_edit_summary is None
    assert new_version.published_at is None
    assert not new_version.published
    assert mock_rdu_user.email == new_version.created_by
    assert new_version.latest

    assert not new_version.get_previous_version().latest

    next_version = page_service.create_copy(
        stub_measure_page.guid, stub_measure_page.version, "major", mock_rdu_user.email
    )

    assert not next_version.get_previous_version().latest

    assert next_version.version == "2.0"
    assert next_version.status == "DRAFT"
    assert next_version.internal_edit_summary is None
    assert next_version.external_edit_summary is None
    assert next_version.published_at is None
    assert not next_version.published
    assert mock_rdu_user.email == new_version.created_by
    assert next_version.latest


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


def test_create_new_version_of_page_duplicates_dimensions(db, db_session, stub_page_with_dimension, mock_rdu_user):
    # given an existing page with a dimension
    assert stub_page_with_dimension.latest
    assert stub_page_with_dimension.dimensions.count() > 0
    old_dimension = stub_page_with_dimension.dimensions[0]
    original_guid = old_dimension.guid
    original_version = old_dimension.page_version

    # when we copy the page
    new_version = page_service.create_copy(
        stub_page_with_dimension.guid, stub_page_with_dimension.version, "minor", mock_rdu_user.email
    )

    # then
    assert new_version.dimensions.count() > 0
    new_dimension = new_version.dimensions[0]
    # new dimension should be a copy
    assert new_dimension.title == old_dimension.title

    # with guid and versions updated
    assert new_dimension.guid != original_guid
    assert new_dimension.page_version != original_version
    assert new_dimension.page_version == new_version.version


def test_create_new_version_of_page_duplicates_dimension_categorisations(
    db, db_session, stub_page_with_dimension, stub_classification, mock_rdu_user
):
    # given an existing page with a dimension
    classification_id = stub_classification.id
    original_dimension_guid = stub_page_with_dimension.dimensions[0].guid
    include_parents = True
    include_all = False
    include_unknown = True

    link = DimensionClassification(
        dimension_guid=original_dimension_guid,
        classification_id=classification_id,
        includes_parents=include_parents,
        includes_unknown=include_unknown,
        includes_all=include_all,
    )
    db_session.session.add(link)
    db_session.session.commit()
    assert stub_page_with_dimension.dimensions[0].classification_links.count() > 0

    # when we copy the page
    new_version = page_service.create_copy(
        stub_page_with_dimension.guid, stub_page_with_dimension.version, "minor", mock_rdu_user.email
    )

    # then
    assert new_version.dimensions.count() > 0
    assert new_version.dimensions[0].classification_links.count() > 0

    new_link = new_version.dimensions[0].classification_links[0]
    assert new_link.dimension_guid == new_version.dimensions[0].guid
    assert new_link.classification_id == classification_id
    assert new_link.includes_parents == include_parents
    assert new_link.includes_all == include_all
    assert new_link.includes_unknown == include_unknown


def test_create_copy_of_page(stub_measure_page, mock_rdu_user):
    assert stub_measure_page.latest

    first_copy = page_service.create_copy(
        stub_measure_page.guid, stub_measure_page.version, "copy", mock_rdu_user.email
    )
    first_copy_guid = first_copy.guid
    first_copy_title = first_copy.title
    first_copy_slug = first_copy.slug

    assert first_copy.version == "1.0"
    assert first_copy.status == "DRAFT"
    assert first_copy.internal_edit_summary is None
    assert first_copy.external_edit_summary is None
    assert first_copy.published_at is None
    assert not first_copy.published
    assert mock_rdu_user.email == first_copy.created_by
    assert first_copy.latest

    second_copy = page_service.create_copy(first_copy.guid, first_copy.version, "copy", mock_rdu_user.email)

    assert second_copy.version == "1.0"
    assert second_copy.status == "DRAFT"
    assert second_copy.internal_edit_summary is None
    assert second_copy.external_edit_summary is None
    assert second_copy.published_at is None
    assert not second_copy.published
    assert mock_rdu_user.email == first_copy.created_by
    assert second_copy.latest

    assert first_copy_guid != second_copy.guid
    assert second_copy.title == f"COPY OF {first_copy_title}"
    assert second_copy.slug == f"{first_copy_slug}-copy"

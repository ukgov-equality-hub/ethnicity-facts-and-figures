from datetime import datetime
import uuid

import pytest

from application.cms.forms import MeasurePageForm
from application.cms.models import Topic, Subtopic, Measure, MeasureVersion, NewVersionType, DimensionClassification
from application.cms.new_page_service import NewPageService
from application.cms.page_service import PageService
from application.cms.exceptions import PageNotFoundException, InvalidPageHierarchy, PageExistsException, PageUnEditable

new_page_service = NewPageService()
page_service = PageService()


class TestNewPageService:
    def test_get_topic_finds_topic_by_slug(self, stub_topic):
        assert new_page_service.get_topic(stub_topic.slug) == stub_topic

    def test_get_topic_raises_if_no_topic_found(self, stub_topic):
        with pytest.raises(PageNotFoundException):
            new_page_service.get_topic("not-the-right-slug")

    def test_get_subtopic_finds_subtopic_by_slug(self, stub_topic, stub_subtopic):
        assert new_page_service.get_subtopic(stub_topic.slug, stub_subtopic.slug) == stub_subtopic

    def test_get_topic_raises_if_no_subtopic_found_in_topic(self, stub_topic, stub_subtopic):
        with pytest.raises(PageNotFoundException):
            new_page_service.get_subtopic("not-the-right-topic", stub_subtopic.slug)

    def test_get_measure_finds_measure_by_slug(self, stub_topic, stub_subtopic, stub_measure_1):
        stub_measure_1.subtopics = [stub_subtopic]

        assert new_page_service.get_measure(stub_topic.slug, stub_subtopic.slug, stub_measure_1.slug) == stub_measure_1

    def test_get_measure_raises_if_no_measure_found_in_subtopic(self, stub_topic, stub_subtopic, stub_measure_1):
        stub_measure_1.subtopics = [stub_subtopic]

        with pytest.raises(PageNotFoundException):
            new_page_service.get_measure("not-the-right-topic", stub_subtopic.slug, stub_measure_1.slug)

    def test_get_measure_version_gets_measure_version_if_hierarchy_is_good(
        self, stub_topic, stub_subtopic, stub_measure_1, stub_measure_version
    ):
        stub_measure_1.subtopics = [stub_subtopic]
        stub_measure_version.measure = stub_measure_1

        assert (
            new_page_service.get_measure_version(
                stub_topic.slug, stub_subtopic.slug, stub_measure_1.slug, stub_measure_version.version
            )
            == stub_measure_version
        )

    def test_get_measure_version_raises_if_hierarchy_is_bad(
        self, stub_topic, stub_subtopic, stub_measure_1, stub_measure_version
    ):
        stub_measure_1.subtopics = [stub_subtopic]
        stub_measure_version.measure = stub_measure_1

        with pytest.raises(PageNotFoundException):
            new_page_service.get_measure_version(
                stub_topic.slug, "not-the-right-subtopic", stub_measure_1.slug, stub_measure_version.version
            )

    def test_get_measure_from_measure_version_id(self, stub_measure_1, stub_measure_version):
        assert new_page_service.get_measure_from_measure_version_id(stub_measure_version.id) == stub_measure_1

    def test_get_measure_from_measure_version_id_raises_if_not_found(self, stub_measure_1, stub_measure_version):
        with pytest.raises(PageNotFoundException):
            new_page_service.get_measure_from_measure_version_id(stub_measure_version.id + 314_159_265)

    def test_get_measure_page_hierarchy_gets_if_hierarchy_is_good(
        self, stub_topic, stub_subtopic, stub_measure_1, stub_measure_version, stub_dimension, stub_upload
    ):
        stub_measure_1.subtopics = [stub_subtopic]
        stub_measure_version.measure = stub_measure_1

        assert list(
            new_page_service.get_measure_page_hierarchy(
                stub_topic.slug, stub_subtopic.slug, stub_measure_1.slug, stub_measure_version.version
            )
        ) == [stub_topic, stub_subtopic, stub_measure_1, stub_measure_version]

        assert list(
            new_page_service.get_measure_page_hierarchy(
                stub_topic.slug,
                stub_subtopic.slug,
                stub_measure_1.slug,
                stub_measure_version.version,
                dimension_guid=stub_dimension.guid,
            )
        ) == [stub_topic, stub_subtopic, stub_measure_1, stub_measure_version, stub_dimension]

        assert list(
            new_page_service.get_measure_page_hierarchy(
                stub_topic.slug,
                stub_subtopic.slug,
                stub_measure_1.slug,
                stub_measure_version.version,
                upload_guid=stub_upload.guid,
            )
        ) == [stub_topic, stub_subtopic, stub_measure_1, stub_measure_version, stub_upload]

        assert list(
            new_page_service.get_measure_page_hierarchy(
                stub_topic.slug,
                stub_subtopic.slug,
                stub_measure_1.slug,
                stub_measure_version.version,
                dimension_guid=stub_dimension.guid,
                upload_guid=stub_upload.guid,
            )
        ) == [stub_topic, stub_subtopic, stub_measure_1, stub_measure_version, stub_dimension, stub_upload]

    def test_get_measure_page_hierarchy_raises_if_hierarchy_is_bad(
        self, stub_topic, stub_subtopic, stub_measure_1, stub_measure_2, stub_measure_version, stub_dimension
    ):
        stub_measure_1.subtopics = [stub_subtopic]
        stub_measure_version.measure = stub_measure_2  # But we make the call with stub_measure_1's slug

        with pytest.raises(InvalidPageHierarchy):
            new_page_service.get_measure_page_hierarchy(
                stub_topic.slug, stub_subtopic.slug, stub_measure_1.slug, stub_measure_version.version
            )

    def test_get_latest_version_of_all_measures(self, db_session):
        topic = Topic(slug="topic-1", title="Topic 1")
        db_session.session.add(topic)
        db_session.session.flush()

        subtopic = Subtopic(slug="subtopic-1", title="Subtopic 1", topic_id=topic.id)
        db_session.session.add(subtopic)
        db_session.session.flush()

        measure_1 = Measure(slug="measure-1")
        measure_1.subtopics = [subtopic]
        db_session.session.add(measure_1)
        db_session.session.flush()

        measure_2 = Measure(slug="measure-2")
        measure_2.subtopics = [subtopic]
        db_session.session.add(measure_2)
        db_session.session.flush()

        measure_1_version_1_0 = MeasureVersion(
            guid=str(uuid.uuid4()),
            version="1.0",
            title="Measure 1 version 1.0",
            published=True,
            measure_id=measure_1.id,
        )
        measure_1_version_2_0 = MeasureVersion(
            guid=str(uuid.uuid4()),
            version="2.0",
            title="Measure 1 version 2.0",
            published=True,
            measure_id=measure_1.id,
        )
        measure_1_version_2_1 = MeasureVersion(
            guid=str(uuid.uuid4()),
            version="2.1",
            title="Measure 1 version 2.1",
            published=False,
            measure_id=measure_1.id,
        )

        measure_2_version_1_0 = MeasureVersion(
            guid=str(uuid.uuid4()),
            version="1.0",
            title="Measure 2 version 1.0",
            published=True,
            measure_id=measure_2.id,
        )
        measure_2_version_2_0 = MeasureVersion(
            guid=str(uuid.uuid4()),
            version="2.0",
            title="Measure 2 version 2.0",
            published=False,
            measure_id=measure_2.id,
        )

        db_session.session.add(measure_1_version_1_0)
        db_session.session.add(measure_1_version_2_0)
        db_session.session.add(measure_1_version_2_1)
        db_session.session.add(measure_2_version_1_0)
        db_session.session.add(measure_2_version_2_0)
        db_session.session.commit()

        assert new_page_service.get_latest_version_of_all_measures(include_drafts=False) == [
            measure_1_version_2_0,
            measure_2_version_1_0,
        ]

        assert new_page_service.get_latest_version_of_all_measures(include_drafts=True) == [
            measure_1_version_2_1,
            measure_2_version_2_0,
        ]

    def test_create_page(self, db_session, stub_subtopic, stub_subtopic_page, test_app_editor):
        created_page = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(title="I care", published_at=datetime.now().date()),
            data_source_forms=[],
            created_by_email=test_app_editor.email,
        )

        assert created_page.title == "I care"
        assert created_page.created_by == test_app_editor.email

    def test_create_page_creates_measure_entry(self, db_session, stub_subtopic, stub_subtopic_page, test_app_editor):
        created_measure_version = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(
                title="I care", published_at=datetime.now().date(), internal_reference="abc123"
            ),
            data_source_forms=[],
            created_by_email=test_app_editor.email,
        )

        created_measure = Measure.query.get(created_measure_version.measure_id)
        assert created_measure.slug == created_measure_version.slug
        assert created_measure.position == len(stub_subtopic.measures) - 1
        assert created_measure.reference == "abc123"
        assert created_measure_version.slug == "i-care"
        assert created_measure_version.internal_reference == "abc123"

    def test_create_page_with_title_and_slug_already_exists_under_subtopic_raises_exception(
        self, db_session, stub_subtopic, stub_subtopic_page, test_app_editor
    ):
        created_page = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(title="I care", published_at=datetime.now().date()),
            data_source_forms=[],
            created_by_email=test_app_editor.email,
        )

        with pytest.raises(PageExistsException):
            new_page_service.create_measure(
                subtopic=stub_subtopic,
                measure_page_form=MeasurePageForm(title=created_page.title, published_at=created_page.published_at),
                data_source_forms=[],
                created_by_email=test_app_editor.email,
            )

    def test_create_page_trims_whitespace(self, db_session, stub_subtopic, stub_subtopic_page, test_app_editor):
        page = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(
                title="\n\t   I care\n", published_at=datetime.now().date(), methodology="\n\n\n\n\n\n"
            ),
            created_by_email=test_app_editor.email,
            data_source_forms=[],
        )

        assert page.title == "I care"
        assert page.methodology is None

    def test_first_version_of_page_title_and_url_match(self, stub_subtopic, stub_subtopic_page, test_app_editor):
        created_page = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(title="the title", published_at=datetime.now().date()),
            created_by_email=test_app_editor.email,
            data_source_forms=[],
        )

        assert "the title" == created_page.title
        assert "the-title" == created_page.slug == created_page.slug

        updated_page = new_page_service.update_measure_version(
            created_page,
            measure_page_form=MeasurePageForm(title="an updated title", db_version_id=created_page.db_version_id),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        assert "an updated title" == updated_page.title
        assert "an-updated-title" == updated_page.slug

    def test_draft_versions_of_page_after_first_title_can_be_changed_without_url_changing(
        self, stub_subtopic, stub_subtopic_page, test_app_editor
    ):
        created_page = new_page_service.create_measure(
            subtopic=stub_subtopic,
            measure_page_form=MeasurePageForm(title="the title", published_at=datetime.now().date()),
            created_by_email=test_app_editor.email,
            data_source_forms=[],
        )

        assert "the title" == created_page.title
        assert "the-title" == created_page.slug

        new_page_service.update_measure_version(
            created_page,
            measure_page_form=MeasurePageForm(
                title="the title", status="APPROVED", db_version_id=created_page.db_version_id
            ),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        copied_page = new_page_service.create_new_measure_version(
            created_page, NewVersionType.MINOR_UPDATE, user=test_app_editor
        )

        assert "the title" == copied_page.title
        assert "the-title" == copied_page.slug

        new_page_service.update_measure_version(
            copied_page,
            measure_page_form=MeasurePageForm(title="the updated title", db_version_id=copied_page.db_version_id),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        assert "the updated title" == copied_page.title
        assert "the-title" == copied_page.slug

    def test_create_new_version_of_page(self, db_session, stub_measure_version, mock_rdu_user):
        assert stub_measure_version.latest is True

        new_version = new_page_service.create_new_measure_version(
            stub_measure_version, NewVersionType.MINOR_UPDATE, user=mock_rdu_user
        )

        assert new_version.version == "1.1"
        assert new_version.status == "DRAFT"
        assert new_version.internal_edit_summary is None
        assert new_version.external_edit_summary is None
        assert new_version.published_at is None
        assert new_version.published is False
        assert mock_rdu_user.email == new_version.created_by
        assert new_version.latest is True

        assert new_version.get_previous_version().latest is False

        next_version = new_page_service.create_new_measure_version(
            stub_measure_version, NewVersionType.MAJOR_UPDATE, user=mock_rdu_user
        )

        assert next_version.get_previous_version().latest is False

        assert next_version.version == "2.0"
        assert next_version.status == "DRAFT"
        assert next_version.internal_edit_summary is None
        assert next_version.external_edit_summary is None
        assert next_version.published_at is None
        assert next_version.published is False
        assert mock_rdu_user.email == new_version.created_by
        assert next_version.latest is True

    def test_create_new_version_of_page_duplicates_dimensions(
        self, db_session, stub_measure_version, stub_dimension, mock_rdu_user
    ):
        # given an existing page with a dimension
        assert stub_measure_version.latest
        assert stub_measure_version.dimensions.count() > 0
        old_dimension = stub_measure_version.dimensions[0]
        original_guid = old_dimension.guid
        original_version = old_dimension.page_version

        # when we copy the page
        new_version = new_page_service.create_new_measure_version(
            stub_measure_version, NewVersionType.MINOR_UPDATE, user=mock_rdu_user
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
        self, db_session, stub_measure_version, stub_dimension, stub_classification, mock_rdu_user
    ):
        # given an existing page with a dimension
        classification_id = stub_classification.id
        original_dimension_guid = stub_measure_version.dimensions[0].guid
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
        assert stub_measure_version.dimensions[0].classification_links.count() > 0

        # when we copy the page
        new_version = new_page_service.create_new_measure_version(
            stub_measure_version, NewVersionType.MINOR_UPDATE, user=mock_rdu_user
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

    def test_create_copy_of_page(self, stub_measure_page, mock_rdu_user):
        assert stub_measure_page.latest

        first_copy = new_page_service.create_new_measure_version(
            stub_measure_page, NewVersionType.NEW_MEASURE, user=mock_rdu_user
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

        second_copy = new_page_service.create_new_measure_version(
            first_copy, NewVersionType.NEW_MEASURE, user=mock_rdu_user
        )

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

    def test_update_measure_version(self, db_session, stub_measure_page, test_app_editor):
        new_page_service.update_measure_version(
            stub_measure_page,
            measure_page_form=MeasurePageForm(title="I care too much!", db_version_id=stub_measure_page.db_version_id),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        measure_version_from_db = new_page_service.get_measure_version_by_id(
            stub_measure_page.measure.id, stub_measure_page.version
        )
        assert measure_version_from_db.title == "I care too much!"
        assert measure_version_from_db.last_updated_by == test_app_editor.email

    def test_update_measure_version_raises_if_page_not_editable(self, db_session, stub_measure_page, test_app_editor):
        measure_version_from_db = new_page_service.get_measure_version_by_id(
            stub_measure_page.measure.id, stub_measure_page.version
        )
        assert measure_version_from_db.status == "DRAFT"

        new_page_service.update_measure_version(
            stub_measure_page,
            measure_page_form=MeasurePageForm(title="Who cares", db_version_id=stub_measure_page.db_version_id),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
            **{"status": "APPROVED"},
        )

        measure_version_from_db = new_page_service.get_measure_version_by_id(
            stub_measure_page.measure.id, stub_measure_page.version
        )
        assert measure_version_from_db.status == "APPROVED"

        with pytest.raises(PageUnEditable):
            new_page_service.update_measure_version(
                stub_measure_page,
                measure_page_form=MeasurePageForm(
                    title="I care too much!", db_version_id=stub_measure_page.db_version_id
                ),
                data_source_forms=[],
                last_updated_by_email=test_app_editor.email,
            )

    def test_update_measure_version_trims_whitespace(self, db_session, stub_measure_page, test_app_editor):
        measure_version = new_page_service.update_measure_version(
            stub_measure_page,
            measure_page_form=MeasurePageForm(
                title="Who cares",
                db_version_id=stub_measure_page.db_version_id,
                published_at=datetime.now().date(),
                ethnicity_definition_summary="\n\n\n\n\n\nThis is what should be left\n",
            ),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        assert measure_version.ethnicity_definition_summary == "This is what should be left"

        new_page_service.update_measure_version(
            stub_measure_page,
            measure_page_form=MeasurePageForm(
                title="Who cares",
                db_version_id=stub_measure_page.db_version_id,
                ethnicity_definition_summary="\n   How about some more whitespace? \n             \n",
            ),
            data_source_forms=[],
            last_updated_by_email=test_app_editor.email,
        )

        measure_version_from_db = new_page_service.get_measure_version_by_id(
            stub_measure_page.measure.id, stub_measure_page.version
        )
        assert measure_version_from_db.ethnicity_definition_summary == "How about some more whitespace?"

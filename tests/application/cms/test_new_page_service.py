from datetime import datetime
import uuid

import pytest

from application.cms.forms import MeasurePageForm
from application.cms.models import Topic, Subtopic, Measure, MeasureVersion
from application.cms.new_page_service import NewPageService
from application.cms.page_service import PageService
from application.cms.exceptions import PageNotFoundException, InvalidPageHierarchy, PageExistsException

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
            new_page_service.get_measure_from_measure_version_id(stub_measure_version.id + 314159265)

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

        updated_page = page_service.update_page(
            created_page,
            data={"title": "an updated title", "db_version_id": created_page.db_version_id},
            last_updated_by=test_app_editor.email,
            data_source_forms=[],
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

        page_service.update_page(
            created_page,
            data={"title": "the title", "status": "APPROVED", "db_version_id": created_page.db_version_id},
            last_updated_by=test_app_editor.email,
            data_source_forms=[],
        )

        copied_page = page_service.create_copy(created_page.guid, created_page.version, "minor", test_app_editor.email)

        assert "the title" == copied_page.title
        assert "the-title" == copied_page.slug

        page_service.update_page(
            copied_page,
            data={"title": "the updated title", "db_version_id": copied_page.db_version_id},
            last_updated_by=test_app_editor.email,
            data_source_forms=[],
        )

        assert "the updated title" == copied_page.title
        assert "the-title" == copied_page.slug

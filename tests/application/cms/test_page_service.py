from datetime import datetime

import pytest

from application.auth.models import TypeOfUser
from application.cms.exceptions import PageNotFoundException, InvalidPageHierarchy, PageExistsException, PageUnEditable
from application.cms.forms import MeasureVersionForm
from application.cms.models import Measure, NewVersionType, DataSource
from application.cms.page_service import PageService
from tests.models import (
    TopicFactory,
    SubtopicFactory,
    MeasureFactory,
    MeasureVersionFactory,
    MeasureVersionWithDimensionFactory,
    UserFactory,
)

page_service = PageService()


class TestPageService:
    def test_get_topic_finds_topic_by_slug(self):
        topic = TopicFactory(slug="topic-slug")
        assert page_service.get_topic("topic-slug") is topic

    def test_get_topic_raises_if_no_topic_found(self):
        TopicFactory(slug="topic-slug")
        with pytest.raises(PageNotFoundException):
            page_service.get_topic("not-the-right-slug")

    def test_get_subtopic_finds_subtopic_by_slug(self):
        subtopic = SubtopicFactory(slug="subtopic-slug", topic__slug="topic-slug")
        assert page_service.get_subtopic("topic-slug", "subtopic-slug") is subtopic

    def test_get_subtopic_raises_if_wrong_topic_slug(self):
        SubtopicFactory(slug="subtopic-slug", topic__slug="topic-slug")
        with pytest.raises(PageNotFoundException):
            page_service.get_subtopic("not-the-right-topic", "subtopic-slug")

    def test_get_measure_finds_measure_by_slug(self):
        measure = MeasureFactory(
            slug="measure-slug", subtopics__slug="subtopic-slug", subtopics__topic__slug="topic-slug"
        )
        assert page_service.get_measure("topic-slug", "subtopic-slug", "measure-slug") is measure

    def test_get_measure_raises_if_wrong_topic_slug(self):
        MeasureFactory(slug="measure-slug", subtopics__slug="subtopic-slug", subtopics__topic__slug="topic-slug")
        with pytest.raises(PageNotFoundException):
            page_service.get_measure("not-the-right-topic", "subtopic-slug", "measure-slug")

    def test_get_measure_raises_if_wrong_subtopic_slug(self):
        MeasureFactory(slug="measure-slug", subtopics__slug="subtopic-slug", subtopics__topic__slug="topic-slug")
        with pytest.raises(PageNotFoundException):
            page_service.get_measure("topic-slug", "not-the-right-subtopic", "measure-slug")

    def test_get_measure_version_gets_measure_version_if_hierarchy_is_good(self):
        measure_version = MeasureVersionFactory()

        assert (
            page_service.get_measure_version(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                measure_version.measure.slug,
                measure_version.version,
            )
            is measure_version
        )

    def test_get_measure_version_raises_if_hierarchy_is_bad(self):
        measure_version = MeasureVersionFactory(measure__subtopics__slug="subtopic-slug")

        with pytest.raises(PageNotFoundException):
            page_service.get_measure_version(
                measure_version.measure.subtopic.topic.slug,
                "not-the-right-subtopic",
                measure_version.measure.slug,
                measure_version.version,
            )

    def test_get_measure_from_measure_version_id(self):
        measure_version = MeasureVersionFactory(id=345)
        assert page_service.get_measure_from_measure_version_id(345) is measure_version.measure

    def test_get_measure_from_measure_version_id_raises_if_not_found(self):
        MeasureVersionFactory(id=345)
        with pytest.raises(PageNotFoundException):
            page_service.get_measure_from_measure_version_id(456)

    def test_get_measure_version_by_id(self):
        measure_version = MeasureVersionFactory(id=345)
        assert page_service.get_measure_version_by_id(345) is measure_version

    def test_get_measure_version_by_id_raises_if_not_found(self):
        MeasureVersionFactory(id=345)
        with pytest.raises(PageNotFoundException):
            page_service.get_measure_version_by_id(456)

    def test_get_measure_page_hierarchy_gets_if_hierarchy_is_good(self):
        measure_version = MeasureVersionWithDimensionFactory()

        assert list(
            page_service.get_measure_version_hierarchy(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                measure_version.measure.slug,
                measure_version.version,
            )
        ) == [
            measure_version.measure.subtopic.topic,
            measure_version.measure.subtopic,
            measure_version.measure,
            measure_version,
        ]

        assert list(
            page_service.get_measure_version_hierarchy(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                measure_version.measure.slug,
                measure_version.version,
                dimension_guid=measure_version.dimensions[0].guid,
            )
        ) == [
            measure_version.measure.subtopic.topic,
            measure_version.measure.subtopic,
            measure_version.measure,
            measure_version,
            measure_version.dimensions[0],
        ]

        assert list(
            page_service.get_measure_version_hierarchy(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                measure_version.measure.slug,
                measure_version.version,
                upload_guid=measure_version.uploads[0].guid,
            )
        ) == [
            measure_version.measure.subtopic.topic,
            measure_version.measure.subtopic,
            measure_version.measure,
            measure_version,
            measure_version.uploads[0],
        ]

        assert list(
            page_service.get_measure_version_hierarchy(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                measure_version.measure.slug,
                measure_version.version,
                dimension_guid=measure_version.dimensions[0].guid,
                upload_guid=measure_version.uploads[0].guid,
            )
        ) == [
            measure_version.measure.subtopic.topic,
            measure_version.measure.subtopic,
            measure_version.measure,
            measure_version,
            measure_version.dimensions[0],
            measure_version.uploads[0],
        ]

    def test_get_measure_page_hierarchy_raises_if_hierarchy_is_bad(self):
        measure_version = MeasureVersionWithDimensionFactory(measure__slug="measure-slug")

        with pytest.raises(InvalidPageHierarchy):
            page_service.get_measure_version_hierarchy(
                measure_version.measure.subtopic.topic.slug,
                measure_version.measure.subtopic.slug,
                "not-the-right-slug",
                measure_version.version,
            )

    def test_get_latest_version_of_all_measures(self):
        measure_1_version_1_0 = MeasureVersionFactory(version="1.0", status="APPROVED", title="Measure 1 version 1.0")
        measure_1_version_2_0 = MeasureVersionFactory(
            version="2.0", status="DRAFT", title="Measure 1 version 2.1", measure=measure_1_version_1_0.measure
        )

        measure_2_version_1_0 = MeasureVersionFactory(
            version="1.0",
            status="APPROVED",
            title="Measure 2 version 1.0",
            measure__subtopics=measure_1_version_1_0.measure.subtopics,
        )
        measure_2_version_1_1 = MeasureVersionFactory(
            version="1.1", status="APPROVED", title="Measure 2 version 2.0", measure=measure_2_version_1_0.measure
        )

        assert page_service.get_latest_version_of_all_measures(include_not_published=False) == [
            measure_1_version_1_0,
            measure_2_version_1_1,
        ]

        assert page_service.get_latest_version_of_all_measures(include_not_published=True) == [
            measure_1_version_2_0,
            measure_2_version_1_1,
        ]

    def test_create_measure(self):
        subtopic = SubtopicFactory()
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        created_measure_version = page_service.create_measure(
            subtopic=subtopic,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False, title="I care", published_at=datetime.now().date(), internal_reference="abc123"
            ),
            created_by_email=user.email,
        )

        assert created_measure_version.title == "I care"
        assert created_measure_version.created_by == user.email
        # # TODO: remove this once MeasureVersions don't have reference
        assert created_measure_version.internal_reference == "abc123"

        created_measure = Measure.query.get(created_measure_version.measure_id)
        assert created_measure.slug == "i-care"
        assert created_measure.position == len(subtopic.measures) - 1
        assert created_measure.reference == "abc123"

    def test_create_page_with_title_and_slug_already_exists_under_subtopic_raises_exception(self):
        subtopic = SubtopicFactory()
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        created_measure_version = page_service.create_measure(
            subtopic=subtopic,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False, title="I care", published_at=datetime.now().date()
            ),
            created_by_email=user.email,
        )

        with pytest.raises(PageExistsException):
            page_service.create_measure(
                subtopic=subtopic,
                measure_version_form=MeasureVersionForm(
                    is_minor_update=False,
                    title=created_measure_version.title,
                    published_at=created_measure_version.published_at,
                ),
                created_by_email=user.email,
            )

    def test_create_page_trims_whitespace(self):
        subtopic = SubtopicFactory()
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        created_measure_version = page_service.create_measure(
            subtopic=subtopic,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False,
                title="\n\t   I care\n",
                published_at=datetime.now().date(),
                methodology="\n\n\n\n\n\n",
            ),
            created_by_email=user.email,
        )

        assert created_measure_version.title == "I care"
        assert created_measure_version.methodology is None

    def test_first_version_of_page_title_and_url_match(self):
        subtopic = SubtopicFactory()
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        created_measure_version = page_service.create_measure(
            subtopic=subtopic,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False, title="the title", published_at=datetime.now().date()
            ),
            created_by_email=user.email,
        )

        assert "the title" == created_measure_version.title
        assert "the-title" == created_measure_version.measure.slug

        updated_measure_version = page_service.update_measure_version(
            created_measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=True, title="an updated title", db_version_id=created_measure_version.db_version_id
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        assert "an updated title" == updated_measure_version.title
        assert "an-updated-title" == updated_measure_version.measure.slug

    def test_draft_versions_of_page_after_first_title_can_be_changed_without_url_changing(self):
        subtopic = SubtopicFactory()
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        created_measure_version = page_service.create_measure(
            subtopic=subtopic,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False, title="the title", published_at=datetime.now().date()
            ),
            created_by_email=user.email,
        )

        assert "the title" == created_measure_version.title
        assert "the-title" == created_measure_version.measure.slug

        page_service.update_measure_version(
            created_measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=True,
                title="the title",
                status="APPROVED",
                db_version_id=created_measure_version.db_version_id,
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        copied_measure_version = page_service.create_measure_version(
            created_measure_version, NewVersionType.MINOR_UPDATE, user=user
        )

        assert "the title" == copied_measure_version.title
        assert "the-title" == copied_measure_version.measure.slug

        page_service.update_measure_version(
            copied_measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=True, title="the updated title", db_version_id=copied_measure_version.db_version_id
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        assert "the updated title" == copied_measure_version.title
        assert "the-title" == copied_measure_version.measure.slug

    def test_create_new_version_of_page(self):
        measure_version = MeasureVersionFactory(latest=True)
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        assert measure_version.latest is True

        new_version = page_service.create_measure_version(measure_version, NewVersionType.MINOR_UPDATE, user=user)

        assert new_version.version == "1.1"
        assert new_version.status == "DRAFT"
        assert new_version.internal_edit_summary is None
        assert new_version.external_edit_summary is None
        assert new_version.published_at is None
        assert user.email == new_version.created_by
        assert new_version.latest is True

        assert new_version.get_previous_version().latest is False

        next_version = page_service.create_measure_version(measure_version, NewVersionType.MAJOR_UPDATE, user=user)

        assert next_version.get_previous_version().latest is False

        assert next_version.version == "2.0"
        assert next_version.status == "DRAFT"
        assert next_version.internal_edit_summary is None
        assert next_version.external_edit_summary is None
        assert next_version.published_at is None
        assert user.email == new_version.created_by
        assert next_version.latest is True

    def test_create_new_version_of_page_duplicates_dimensions(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionWithDimensionFactory(latest=True)

        assert measure_version.latest
        assert measure_version.dimensions.count() > 0
        old_dimension = measure_version.dimensions[0]
        old_dimension_guid = old_dimension.guid

        new_version = page_service.create_measure_version(measure_version, NewVersionType.MINOR_UPDATE, user=user)

        assert new_version.dimensions.count() > 0
        new_dimension = new_version.dimensions[0]

        assert old_dimension.title == new_dimension.title
        assert old_dimension_guid != new_dimension.guid
        assert measure_version is not new_dimension.measure_version

    def test_create_new_version_of_page_duplicates_dimension_categorisations(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        # given an existing page with a dimension with known classification
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__classification_links__classification__id="my-classification",
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=True,
            dimensions__classification_links__includes_unknown=True,
        )

        assert measure_version.dimensions[0].classification_links.count() > 0

        # when we copy the page
        new_version = page_service.create_measure_version(measure_version, NewVersionType.MINOR_UPDATE, user=user)

        # then
        assert new_version.dimensions.count() > 0
        assert new_version.dimensions[0].classification_links.count() > 0

        new_link = new_version.dimensions[0].classification_links[0]
        assert new_link.dimension_guid == new_version.dimensions[0].guid
        assert new_link.classification_id == "my-classification"
        assert new_link.includes_parents is False
        assert new_link.includes_all is True
        assert new_link.includes_unknown is True

    def test_create_new_minor_version_duplicates_uploads(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(latest=True)
        assert len(measure_version.uploads) == 1
        original_upload = measure_version.uploads[0]

        new_version = page_service.create_measure_version(measure_version, NewVersionType.MINOR_UPDATE, user=user)

        assert len(new_version.uploads) == 1
        new_upload = new_version.uploads[0]
        assert new_upload.guid != original_upload.guid
        assert new_upload.file_name == original_upload.file_name
        assert new_upload.title == original_upload.title
        assert new_upload.description == original_upload.description

    def test_create_new_major_version_does_not_duplicate_uploads(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(latest=True)

        new_version = page_service.create_measure_version(measure_version, NewVersionType.MAJOR_UPDATE, user=user)

        assert len(measure_version.uploads) == 1
        assert len(new_version.uploads) == 0

    @pytest.mark.parametrize("version_type", [t for t in NewVersionType])
    def test_create_measure_version_creates_associations_rather_than_copies_of_existing_data_sources(
        self, version_type
    ):
        measure_version = MeasureVersionFactory(version="1.0")
        user = UserFactory(user_type=TypeOfUser.RDU_USER)

        assert len(measure_version.data_sources) == 1
        assert DataSource.query.count() == 1

        new_version = page_service.create_measure_version(measure_version, version_type, user=user)

        assert DataSource.query.count() == 1

        if version_type == NewVersionType.MAJOR_UPDATE:
            assert new_version.data_sources == []
        else:
            assert measure_version.data_sources == new_version.data_sources

    def test_create_copy_of_page(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(latest=True, measure__slug="slug")
        assert measure_version.latest

        first_copy = page_service.create_measure_version(measure_version, NewVersionType.NEW_MEASURE, user=user)
        first_copy_measure_id = first_copy.measure_id
        first_copy_title = first_copy.title
        first_copy_slug = first_copy.measure.slug

        assert first_copy.version == "1.0"
        assert first_copy.status == "DRAFT"
        assert first_copy.internal_edit_summary is None
        assert first_copy.external_edit_summary is None
        assert first_copy.published_at is None
        assert first_copy.created_by == user.email
        assert first_copy.latest

        second_copy = page_service.create_measure_version(first_copy, NewVersionType.NEW_MEASURE, user=user)

        assert second_copy.version == "1.0"
        assert second_copy.status == "DRAFT"
        assert second_copy.internal_edit_summary is None
        assert second_copy.external_edit_summary is None
        assert second_copy.published_at is None
        assert user.email == first_copy.created_by
        assert second_copy.latest

        assert first_copy_measure_id != second_copy.measure_id
        assert second_copy.title == f"COPY OF {first_copy_title}"
        assert second_copy.measure.slug == f"{first_copy_slug}-copy"

    def test_update_measure_version(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(version="1.0", status="DRAFT")

        page_service.update_measure_version(
            measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=True, title="I care too much!", db_version_id=measure_version.db_version_id
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        measure_version_from_db = page_service.get_measure_version_by_measure_id_and_version(
            measure_version.measure.id, measure_version.version
        )
        assert measure_version_from_db.title == "I care too much!"
        assert measure_version_from_db.last_updated_by == user.email

    def test_update_measure_version_raises_if_page_not_editable(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(version="1.0", status="DRAFT")

        measure_version_from_db = page_service.get_measure_version_by_measure_id_and_version(
            measure_version.measure.id, measure_version.version
        )
        assert measure_version_from_db.status == "DRAFT"

        page_service.update_measure_version(
            measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=True, title="Who cares", db_version_id=measure_version.db_version_id
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
            **{"status": "APPROVED"},
        )

        measure_version_from_db = page_service.get_measure_version_by_measure_id_and_version(
            measure_version.measure.id, measure_version.version
        )
        assert measure_version_from_db.status == "APPROVED"

        with pytest.raises(PageUnEditable):
            page_service.update_measure_version(
                measure_version,
                measure_version_form=MeasureVersionForm(
                    is_minor_update=True, title="I care too much!", db_version_id=measure_version.db_version_id
                ),
                data_source_forms=[],
                last_updated_by_email=user.email,
            )

    def test_update_measure_version_trims_whitespace(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(version="1.0", status="DRAFT")

        page_service.update_measure_version(
            measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False,
                title="Who cares",
                db_version_id=measure_version.db_version_id,
                published_at=datetime.now().date(),
                ethnicity_definition_summary="\n\n\n\n\n\nThis is what should be left\n",
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        assert measure_version.ethnicity_definition_summary == "This is what should be left"

        page_service.update_measure_version(
            measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False,
                title="Who cares",
                db_version_id=measure_version.db_version_id,
                ethnicity_definition_summary="\n   How about some more whitespace? \n             \n",
            ),
            data_source_forms=[],
            last_updated_by_email=user.email,
        )

        measure_version_from_db = page_service.get_measure_version_by_measure_id_and_version(
            measure_version.measure.id, measure_version.version
        )
        assert measure_version_from_db.ethnicity_definition_summary == "How about some more whitespace?"

    def test_reject_measure_version(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(version="1.0", status="DRAFT")

        assert measure_version.status == "DRAFT"

        page_service.update_measure_version(
            measure_version,
            measure_version_form=MeasureVersionForm(
                is_minor_update=False, title="Who cares", db_version_id=measure_version.db_version_id
            ),
            last_updated_by_email=user.email,
            data_source_forms=[],
            **{"status": "DEPARTMENT_REVIEW"},
        )
        assert measure_version.status == "DEPARTMENT_REVIEW"

        message = page_service.reject_measure_version(measure_version)

        assert message == 'Sent page "Who cares" to REJECTED'
        assert measure_version.status == "REJECTED"

    def test_set_page_to_next_state(self):
        user = UserFactory(user_type=TypeOfUser.RDU_USER)
        measure_version = MeasureVersionFactory(status="DRAFT")

        assert measure_version.status == "DRAFT"

        page_service.move_measure_version_to_next_state(measure_version, updated_by=user.email)
        assert measure_version.status == "INTERNAL_REVIEW"
        assert measure_version.last_updated_by == user.email

        page_service.move_measure_version_to_next_state(measure_version, updated_by=user.email)
        assert measure_version.status == "DEPARTMENT_REVIEW"
        assert measure_version.last_updated_by == user.email

        page_service.move_measure_version_to_next_state(measure_version, updated_by=user.email)
        assert measure_version.status == "APPROVED"
        assert measure_version.last_updated_by == user.email
        assert measure_version.published_by == user.email

    def test_get_latest_publishable_versions_of_measures_for_subtopic(self):
        measure = MeasureFactory()
        version_1_0 = MeasureVersionFactory(version="1.0", status="APPROVED", measure=measure)
        version_1_1 = MeasureVersionFactory(version="1.1", status="APPROVED", measure=measure)
        latest_publishable_version = MeasureVersionFactory(version="1.2", status="APPROVED", measure=measure)
        MeasureVersionFactory(version="1.3", status="DRAFT", measure=measure)

        measure_2 = MeasureFactory(subtopics=measure.subtopics)
        MeasureVersionFactory(version="1.0", status="DRAFT", measure=measure_2)

        measures = page_service.get_publishable_measures_for_subtopic(measure.subtopic)
        assert len(measures) == 1
        assert measures[0] == measure
        assert measure.versions_to_publish == [latest_publishable_version, version_1_1, version_1_0]
        assert measure_2.versions_to_publish == []

    @pytest.mark.parametrize(
        "topic_slugs, include_testing_space, expected_topic_count",
        (
            (["british-population", "health"], False, 2),
            (["british-population", "health"], True, 2),
            (["british-population", "health", "testing-space"], False, 2),
            (["british-population", "health", "testing-space"], True, 3),
        ),
    )
    def test_get_topics(self, topic_slugs, include_testing_space, expected_topic_count):
        for topic_slug in topic_slugs:
            TopicFactory(slug=topic_slug)

        topics = page_service.get_topics(include_testing_space=include_testing_space)

        assert len(topics) == expected_topic_count

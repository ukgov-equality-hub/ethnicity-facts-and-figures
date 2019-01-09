import pytest

from application.cms.new_page_service import NewPageService
from application.cms.exceptions import PageNotFoundException

new_page_service = NewPageService()


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

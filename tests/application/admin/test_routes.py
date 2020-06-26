from flask import url_for


def test_data_sources_route():
    assert url_for("admin.data_sources") == "/admin/data-sources"


def test_merge_data_sources_route():
    assert url_for("admin.merge_data_sources") == "/admin/data-sources/merge"


def test_manage_topics_routes():
    assert url_for("admin.manage_topics") == "/admin/manage-topics"
    assert url_for("admin.edit_topic", topic_id=2) == "/admin/topic/2/edit"
    assert url_for("admin.edit_subtopic", subtopic_id=2) == "/admin/subtopic/2/edit"
    assert url_for("admin.update_topic", topic_id=2) == "/admin/topic/2/update"
    assert url_for("admin.update_subtopic", subtopic_id=2) == "/admin/subtopic/2/update"

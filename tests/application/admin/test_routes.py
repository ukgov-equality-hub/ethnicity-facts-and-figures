from flask import url_for


def test_data_sources_route():
    assert url_for("admin.data_sources") == "/admin/data-sources"


def test_merge_data_sources_route():
    assert url_for("admin.merge_data_sources") == "/admin/data-sources/merge"

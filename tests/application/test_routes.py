from functools import partial
from typing import Set


class TestRoutes:
    @classmethod
    def get_flask_url(cls, endpoint, routes: Set, **kwargs):
        from flask import url_for

        routes.add(endpoint)
        return url_for(endpoint, **kwargs)

    @staticmethod
    def get_endpoints_for_blueprint(app, blueprint_name):
        return set(rule.endpoint for rule in app.url_map.iter_rules() if rule.endpoint.split(".")[0] == blueprint_name)

    def test_admin_routes(self, app):
        routes = set()
        get_url = partial(self.get_flask_url, routes=routes)

        assert get_url("admin.index") == "/admin"
        assert get_url("admin.users") == "/admin/users"
        assert get_url("admin.user_by_id", user_id=1) == "/admin/users/1"
        assert get_url("admin.share_page_with_user", user_id=1) == "/admin/users/1/share"
        assert get_url("admin.remove_shared_page_from_user", user_id=1, measure_id=1) == "/admin/users/1/remove-share/1"
        assert get_url("admin.add_user") == "/admin/users/add"
        assert (
            get_url("admin.resend_account_activation_email", user_id=1)
            == "/admin/users/1/resend-account-activation-email"
        )
        assert get_url("admin.deactivate_user", user_id=1) == "/admin/users/1/deactivate"
        assert get_url("admin.delete_user", user_id=1) == "/admin/users/1/delete"
        assert get_url("admin.make_admin_user", user_id=1) == "/admin/users/1/make-admin"
        assert get_url("admin.make_rdu_user", user_id=1) == "/admin/users/1/make-rdu-user"
        assert get_url("admin.site_build") == "/admin/site-build"
        assert get_url("admin.data_sources") == "/admin/data-sources"

        # Make sure that the routes we've tested above are all of the routes that our app has registered with Flask
        # i.e. that we haven't added a new view and not updated this test to lock the URL path in place.
        all_admin_endpoints = self.get_endpoints_for_blueprint(app, "admin")
        assert routes == all_admin_endpoints, (
            f"Missing assertions for routes in the admin blueprint: "
            f"{routes.symmetric_difference(all_admin_endpoints)}. Please update this test."
        )

    def test_cms_routes(self, app):
        routes = set()
        get_url = partial(self.get_flask_url, routes=routes)

        assert get_url("cms.get_valid_classifications") == "/cms/get-valid-classifications-for-data"
        assert get_url("cms.set_dimension_order") == "/cms/set-dimension-order"
        assert get_url("cms.set_measure_order") == "/cms/set-measure-order"
        assert get_url("cms.index") == "/cms"
        assert (
            get_url(
                "cms.link_existing_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/link"
        )
        assert (
            get_url(
                "cms.new_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/new"
        )
        assert (
            get_url(
                "cms.create_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/new"
        )
        assert (
            get_url(
                "cms.remove_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                data_source_id=1,
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/1/remove"
        )
        assert (
            get_url("cms.create_measure", topic_slug="topic", subtopic_slug="subtopic")
            == "/cms/topic/subtopic/measure/new"
        )
        assert (
            get_url(
                "cms.create_dimension",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension/new"
        )
        assert (
            get_url(
                "cms.delete_upload",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                upload_guid="upload-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/uploads/upload-guid/delete"
        )
        assert (
            get_url(
                "cms.edit_upload",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                upload_guid="upload-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/uploads/upload-guid/edit"
        )
        assert (
            get_url(
                "cms.edit_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                data_source_id=1,
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/1"
        )
        assert (
            get_url(
                "cms.update_data_source",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                data_source_id=1,
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources/1"
        )
        assert (
            get_url(
                "cms.search_data_sources",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/edit/data-sources"
        )
        assert (
            get_url("cms.view_measure_version_by_measure_version_id", measure_version_id=1) == "/cms/measure-version/1"
        )
        assert (
            get_url("cms.list_measure_versions", topic_slug="topic", subtopic_slug="subtopic", measure_slug="measure")
            == "/cms/topic/subtopic/measure/versions"
        )
        assert (
            get_url(
                "cms.new_version", topic_slug="topic", subtopic_slug="subtopic", measure_slug="measure", version="1.0"
            )
            == "/cms/topic/subtopic/measure/1.0/new-version"
        )
        assert (
            get_url(
                "cms.get_measure_version_uploads",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/uploads"
        )
        assert (
            get_url(
                "cms.create_upload", topic_slug="topic", subtopic_slug="subtopic", measure_slug="measure", version="1.0"
            )
            == "/cms/topic/subtopic/measure/1.0/upload"
        )
        assert (
            get_url(
                "cms.confirm_delete_measure_version",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/delete"
        )
        assert (
            get_url(
                "cms.delete_measure_version",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/delete"
        )
        assert (
            get_url(
                "cms.edit_measure_version",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/edit"
        )
        assert (
            get_url(
                "cms.copy_measure_version",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
            )
            == "/cms/topic/subtopic/measure/1.0/copy"
        )
        assert (
            get_url(
                "cms.create_chart",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/create-chart"
        )
        assert (
            get_url(
                "cms.create_table",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/create-table"
        )
        assert (
            get_url(
                "cms.delete_chart",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/delete-chart"
        )
        assert (
            get_url(
                "cms.delete_table",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/delete-table"
        )
        assert (
            get_url(
                "cms.save_chart_to_page",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/save-chart"
        )
        assert (
            get_url(
                "cms.save_table_to_page",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/save-table"
        )
        assert (
            get_url(
                "cms.delete_dimension",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/delete"
        )
        assert (
            get_url(
                "cms.edit_dimension",
                topic_slug="topic",
                subtopic_slug="subtopic",
                measure_slug="measure",
                version="1.0",
                dimension_guid="dimension-guid",
            )
            == "/cms/topic/subtopic/measure/1.0/dimension-guid/edit"
        )

        # Make sure that the routes we've tested above are all of the routes that our app has registered with Flask
        # i.e. that we haven't added a new view and not updated this test to lock the URL path in place.
        all_cms_endpoints = self.get_endpoints_for_blueprint(app, "cms")
        assert routes == all_cms_endpoints, (
            f"Missing assertions for routes in the cms blueprint: "
            f"{routes.symmetric_difference(all_cms_endpoints)}. Please update this test."
        )

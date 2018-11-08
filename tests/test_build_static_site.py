from unittest.mock import patch

from application.sitebuilder.build import do_it
from application.sitebuilder.build_service import request_build
from manage import refresh_materialized_views
from tests.utils import UnexpectedMockInvocationException


def test_static_site_build(
    db_session,
    single_use_app,
    stub_home_page,
    # Including these three versioned pages ensures the build test exercises the logic to build multiple page versions
    stub_measure_page_one_of_three,
    stub_measure_page_two_of_three,
    stub_measure_page_three_of_three,
    stub_page_with_dimension_and_chart_and_table,
):
    """
    A basic test for the core flow of the static site builder. This patches/mocks a few of the key integrations to 
    help prevent calling out to external services accidentally, and where possible, includes two levels of failsafes.
    1) We change the application config to not push/deploy the site
    2) We mock out the push_site, so that even if the config setting fails, this test will raise an error.
    
    Unfortunately, due to circular dependencies between build/build_service, it's not easy to mock out `deploy_site`.
    So we mock out the S3FileSystem, which is initialized within `deloy_site`. This will throw an error if invoked.
    
    `create_versioned_assets` is mocked out because that function is only needed to generate css/js, which is tested
    in a separate step outside of pytest.
    
    `write_html` is mocked out so that we don't need to be able to write to a filesystem.
    
    We should look at expanding test coverage of the static site builder eventually, but such a task should probably
    also include refactoring the site builder to be more modular, less tightly-coupled, and more easy to test.
    """
    with patch.dict(single_use_app.config):
        with patch("application.sitebuilder.build.push_site") as push_site_patch:
            with patch("application.sitebuilder.build.pull_current_site") as pull_current_site_patch:
                with patch("application.sitebuilder.build_service.S3FileSystem") as s3_fs_patch:
                    with patch("application.dashboard.data_helpers.trello_service") as trello_service_patch:
                        with patch("application.sitebuilder.build.create_versioned_assets"):
                            with patch("application.sitebuilder.build.write_html"):
                                single_use_app.config["PUSH_SITE"] = False
                                single_use_app.config["DEPLOY_SITE"] = False
                                pull_current_site_patch.side_effect = UnexpectedMockInvocationException
                                push_site_patch.side_effect = UnexpectedMockInvocationException
                                s3_fs_patch.side_effect = UnexpectedMockInvocationException
                                trello_service_patch.get_measure_cards.return_value = []

                                # We publish this page to ensure there is an item for each of the dashboard views
                                stub_page_with_dimension_and_chart_and_table.status = "APPROVED"
                                db_session.session.add(stub_page_with_dimension_and_chart_and_table)
                                db_session.session.commit()

                                # Materialized views are initially empty - populate them with our fixture page data
                                refresh_materialized_views()

                                do_it(single_use_app, request_build())

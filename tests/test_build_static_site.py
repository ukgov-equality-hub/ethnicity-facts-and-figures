import pytest
import time
from unittest.mock import patch, MagicMock

from application.sitebuilder.build import do_it
from application.sitebuilder.build_service import request_build
from tests.utils import UnexpectedMockInvocationException


def test_static_site_build(single_use_app, stub_home_page, stub_published_measure_page):
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

                                do_it(single_use_app, request_build())

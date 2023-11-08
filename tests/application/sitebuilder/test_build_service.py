from datetime import datetime, timedelta

from unittest.mock import patch

import pytest
import stopit

from application.sitebuilder.build import do_it
from application.sitebuilder.build_service import build_site, request_build
from manage import refresh_materialized_views
from tests.models import MeasureFactory, MeasureVersionWithDimensionFactory
from tests.utils import GeneralTestException, UnexpectedMockInvocationException


def test_build_exceptions_not_suppressed(app):
    with patch("application.sitebuilder.build_service.do_it") as do_it_patch:
        do_it_patch.side_effect = GeneralTestException("build error")

        request_build()

        with pytest.raises(GeneralTestException) as e, stopit.SignalTimeout(2):
            build_site(app)

        assert str(e.value) == "build error"


def test_static_site_build(db_session, single_use_app):
    """
    A basic test for the core flow of the static site builder. This patches/mocks a few of the key integrations to
    help prevent calling out to external services accidentally, and where possible, includes two levels of failsafes.
    1) We change the application config to not push/deploy the site
    2) We mock out the push_site, so that even if the config setting fails, this test will raise an error.

    Unfortunately, due to circular dependencies between build/build_service, it's not easy to mock out `deploy_site`.
    So we mock out the S3FileSystem, which is initialized within `deploy_site`. This will throw an error if invoked.

    `create_versioned_assets` is mocked out because that function is only needed to generate css/js, which is tested
    in a separate step outside of pytest.

    `write_html` is mocked out so that we don't need to be able to write to a filesystem.

    We should look at expanding test coverage of the static site builder eventually, but such a task should probably
    also include refactoring the site builder to be more modular, less tightly-coupled, and more easy to test.
    """
    with patch.dict(single_use_app.config):
        with patch("application.sitebuilder.build_service.S3FileSystem") as s3_fs_patch:
            with patch("application.dashboard.data_helpers.trello_service") as trello_service_patch:
                with patch("application.sitebuilder.build.create_versioned_assets"):
                    with patch("application.sitebuilder.build.write_html"):
                        single_use_app.config["PUSH_SITE"] = False
                        single_use_app.config["DEPLOY_SITE"] = False
                        s3_fs_patch.side_effect = UnexpectedMockInvocationException
                        trello_service_patch.get_measure_cards.return_value = []

                        from tests.test_data.chart_and_table import chart, simple_table

                        # Including these three versioned pages ensures the build test exercises the logic to
                        # build multiple page versions
                        measure = MeasureFactory()
                        # Outdated version
                        MeasureVersionWithDimensionFactory(
                            measure=measure,
                            status="APPROVED",
                            latest=False,
                            published_at=datetime.now().date(),
                            version="1.0",
                            dimensions__dimension_chart=None,
                            dimensions__dimension_table__table_object=simple_table(),
                        )
                        # Latest published version
                        MeasureVersionWithDimensionFactory(
                            measure=measure,
                            status="APPROVED",
                            latest=False,
                            published_at=datetime.now().date(),
                            version="2.0",
                            dimensions__dimension_chart=None,
                            dimensions__dimension_table__table_object=simple_table(),
                        )
                        # Newer draft version
                        MeasureVersionWithDimensionFactory(
                            measure=measure,
                            status="DRAFT",
                            published_at=None,
                            latest=True,
                            version="2.1",
                            dimensions__dimension_chart=None,
                            dimensions__dimension_table=None,
                        )

                        # Publish another page with dimension, chart and table to ensure there's an item for
                        # each of the dashboard views
                        MeasureVersionWithDimensionFactory(
                            status="APPROVED",
                            latest=True,
                            published_at=datetime.now().date() - timedelta(weeks=1),
                            version="1.0",
                            measure__subtopics__topic__slug="topic",
                            measure__subtopics__slug="subtopic",
                            measure__slug="measure",
                            dimensions__guid="dimension-guid",
                            dimensions__dimension_chart__chart_object=chart,
                            dimensions__dimension_table__table_object=simple_table(),
                            uploads__guid="test-download",
                            uploads__title="Test measure page data",
                            uploads__file_name="test-measure-page-data.csv",
                        )

                        # Materialized views are initially empty - populate them with our fixture page data
                        refresh_materialized_views()

                        do_it(single_use_app, request_build())

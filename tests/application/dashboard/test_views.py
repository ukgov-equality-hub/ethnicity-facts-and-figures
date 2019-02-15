from datetime import datetime

import pytest

from manage import refresh_materialized_views
from tests.models import (
    MeasureVersionWithDimensionFactory,
    DataSourceFactory,
    SubtopicFactory,
    SubtopicPageFactory,
    TopicPageFactory,
)


@pytest.mark.parametrize(
    "dashboard_url",
    (
        "/dashboards/",
        "/dashboards/published",
        "/dashboards/ethnic-groups",
        "/dashboards/ethnic-groups/asian",
        "/dashboards/ethnic-groups/indian",
        "/dashboards/ethnic-groups/mixed-white-black-caribbean",
        "/dashboards/ethnicity-classifications",
        "/dashboards/ethnicity-classifications/5A",
        "/dashboards/geographic-breakdown",
    ),
)
def test_dashboard_pages_return_200(test_app_client, logged_in_rdu_user, dashboard_url):
    data_source = DataSourceFactory()
    topic_page = TopicPageFactory(slug="topic-slug")  # TODO: Remove
    subtopic = SubtopicFactory(topic__slug="topic-slug")  # TODO: Remove
    subtopic_page = SubtopicPageFactory(id=subtopic.id, slug=subtopic.slug, parent=topic_page)  # TODO: Remove
    MeasureVersionWithDimensionFactory(
        data_sources=[data_source],
        status="APPROVED",
        published_at=datetime.now().date(),
        parent=subtopic_page,
        dimensions__classification_links__includes_parents=False,
        dimensions__classification_links__includes_all=True,
        dimensions__classification_links__includes_unknown=True,
        dimensions__classification_links__classification__id="5A",
    )
    refresh_materialized_views()

    resp = test_app_client.get(dashboard_url)
    assert resp.status_code == 200, f"Failed to load dashboards '{dashboard_url}'"

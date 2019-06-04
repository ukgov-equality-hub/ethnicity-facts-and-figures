from datetime import datetime
from flask import url_for
from lxml import html

import pytest

from manage import refresh_materialized_views
from tests.models import MeasureFactory, MeasureVersionFactory, MeasureVersionWithDimensionFactory


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
    MeasureVersionWithDimensionFactory(
        status="APPROVED",
        published_at=datetime.now().date(),
        dimensions__classification_links__includes_parents=False,
        dimensions__classification_links__includes_all=True,
        dimensions__classification_links__includes_unknown=True,
        dimensions__classification_links__classification__id="5A",
    )
    refresh_materialized_views()

    resp = test_app_client.get(dashboard_url)
    assert resp.status_code == 200, f"Failed to load dashboards '{dashboard_url}'"


def test_data_corrections_page_with_no_corrections(test_app_client, logged_in_rdu_user):
    resp = test_app_client.get(url_for("static_site.corrections"))
    doc = html.fromstring(resp.get_data(as_text=True))
    assert len(doc.xpath("//div[@class='corrected-measure-version']")) == 0


def test_data_corrections_page_shows_corrected_versions_with_link_to_page_containing_correction(
    test_app_client, logged_in_rdu_user, db_session
):
    measure = MeasureFactory(slug="measure", subtopics__slug="subtopic", subtopics__topic__slug="topic")

    measure_versions = []
    for version, published_at, update_corrects_data_mistake in (
        ("1.0", datetime.fromisoformat("2000-01-01T12:00:00"), False),
        ("1.1", datetime.fromisoformat("2001-01-01T12:00:00"), True),
        ("1.2", datetime.fromisoformat("2002-01-01T12:00:00"), False),
        ("2.0", datetime.fromisoformat("2003-01-01T12:00:00"), False),
    ):
        measure_versions.append(
            MeasureVersionFactory(
                version=version,
                status="APPROVED",
                update_corrects_data_mistake=update_corrects_data_mistake,
                published_at=published_at,
                measure=measure,
            )
        )

    resp = test_app_client.get(url_for("static_site.corrections"))
    doc = html.fromstring(resp.get_data(as_text=True))

    assert len(doc.xpath("//div[@class='corrected-measure-version']")) == 1
    assert "1 January 2001" in doc.xpath("//div[@class='corrected-measure-version']")[0].text_content()
    assert doc.xpath("//div[@class='corrected-measure-version']//h2/a/@href")[0] == "/topic/subtopic/measure/1.1"

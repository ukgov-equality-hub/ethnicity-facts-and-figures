import pytest


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
def test_dashboard_pages_return_200(
    test_app_client,
    mock_rdu_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page,
    dashboard_url,
    two_classifications_2A_5A,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id
    resp = test_app_client.get(dashboard_url)
    assert resp.status_code == 200, f"Failed to load dashboards '{dashboard_url}'"

import pytest


@pytest.mark.parametrize(
    "dashboard_url",
    (
            "/dashboard/",
            "/dashboard/published",
            "/dashboard/ethnic-groups",
            "/dashboard/ethnic-groups/asian",
            "/dashboard/ethnic-groups/indian",
            "/dashboard/ethnic-groups/mixed-white-black-caribbean",
            "/dashboard/ethnicity-categorisations",
            "/dashboard/ethnicity-categorisations/5",
            "/dashboard/ethnicity-categorisations/8",
            "/dashboard/ethnicity-categorisations/13",
            "/dashboard/levels-of-geography",
    )
)
def test_dashboard_pages_return_200(
        test_app_client,
        mock_user,
        stub_topic_page,
        stub_subtopic_page,
        stub_measure_page,
        dashboard_url,
):
    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id
    resp = test_app_client.get(dashboard_url)
    assert resp.status_code == 200, f"Failed to load dashboard '{dashboard_url}'"

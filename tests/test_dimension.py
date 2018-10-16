from bs4 import BeautifulSoup
from flask import url_for

from application.auth.models import User, TypeOfUser
from application.cms.models import Dimension
from application import db


def test_create_valid_dimension(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    data = {"title": "Test dimension"}

    url = url_for(
        "cms.create_dimension",
        topic=stub_measure_page.parent.parent.uri,
        subtopic=stub_measure_page.parent.uri,
        measure=stub_measure_page.uri,
        version=stub_measure_page.version,
    )

    resp = test_app_client.post(url, data=data, follow_redirects=False)

    assert resp.status_code == 302, "Should be redirected to edit page for dimension"


def test_create_dimension_without_specifying_title(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    url = url_for(
        "cms.create_dimension",
        topic=stub_measure_page.parent.parent.uri,
        subtopic=stub_measure_page.parent.uri,
        measure=stub_measure_page.uri,
        version=stub_measure_page.version,
    )

    resp = test_app_client.post(url, follow_redirects=False)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Error: Create dimension"


def test_update_dimension_with_valid_data(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    dimension = Dimension(
        guid="stub_dimension",
        title="Test dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
    )

    stub_measure_page.dimensions.append(dimension)
    db.session.add(dimension)
    db.session.commit()

    data = {"title": "Test dimension"}

    url = url_for(
        "cms.edit_dimension",
        topic=stub_measure_page.parent.parent.uri,
        subtopic=stub_measure_page.parent.uri,
        measure=stub_measure_page.uri,
        version=stub_measure_page.version,
        dimension=dimension.guid,
    )

    resp = test_app_client.post(url, data=data, follow_redirects=False)

    assert resp.status_code == 302, "Should be redirected to edit page for dimension"


def test_update_dimension_with_invalid_data(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    dimension = Dimension(
        guid="stub_dimension",
        title="Test dimension",
        time_period="stub_timeperiod",
        page=stub_measure_page,
        position=stub_measure_page.dimensions.count(),
    )

    stub_measure_page.dimensions.append(dimension)
    db.session.add(dimension)
    db.session.commit()

    data = {"title": ""}

    url = url_for(
        "cms.edit_dimension",
        topic=stub_measure_page.parent.parent.uri,
        subtopic=stub_measure_page.parent.uri,
        measure=stub_measure_page.uri,
        version=stub_measure_page.version,
        dimension=dimension.guid,
    )

    resp = test_app_client.post(url, data=data, follow_redirects=False)

    assert resp.status_code == 200  # TODO: this should ideally be 400.

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("title").string == "Error: Edit dimension"

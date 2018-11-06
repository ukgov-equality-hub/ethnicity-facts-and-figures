import datetime
import json

import pytest
from flask import url_for
from bs4 import BeautifulSoup

from application.auth.models import TypeOfUser
from application.cms.forms import MeasurePageForm
from application.cms.models import Page, Upload
from application.cms.page_service import PageService
from application.sitebuilder.models import Build


def test_create_measure_page(
    test_app_client,
    mock_rdu_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_data,
    stub_frequency,
    stub_geography,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    form = MeasurePageForm(**stub_measure_data)

    resp = test_app_client.post(
        url_for("cms.create_measure_page", topic_uri=stub_topic_page.uri, subtopic_uri=stub_subtopic_page.uri),
        data=form.data,
        follow_redirects=True,
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == "Created page %s" % stub_measure_data["title"]


@pytest.mark.parametrize("cannot_reject_status", ("DRAFT", "APPROVED"))
def test_can_not_reject_page_if_not_under_review(
    app, test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page, cannot_reject_status
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id
    stub_measure_page.status = cannot_reject_status
    response = test_app_client.get(
        url_for(
            "cms.reject_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
            follow_redirects=True,
        )
    )
    assert response.status_code == 400
    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == cannot_reject_status


def test_can_reject_page_under_review(
    app, test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):
    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id
    stub_measure_page.status = "DEPARTMENT_REVIEW"
    test_app_client.get(
        url_for(
            "cms.reject_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
            follow_redirects=True,
        )
    )
    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "REJECTED"


def test_admin_user_can_publish_page_in_dept_review(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page,
    mock_request_build,
    mock_page_service_mark_page_published,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    stub_measure_page.status = "DEPARTMENT_REVIEW"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.publish",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    mock_request_build.assert_called_once()
    mock_page_service_mark_page_published.assert_called_once_with(stub_measure_page)

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "APPROVED"
    assert page.last_updated_by == mock_admin_user.email
    assert page.published_by == mock_admin_user.email
    assert page.publication_date == datetime.date.today()

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == 'Sent page "Test Measure Page" to APPROVED'  # noqa


def test_admin_user_can_not_publish_page_not_in_department_review(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page,
    mock_request_build,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    assert stub_measure_page.status == "DRAFT"

    response = test_app_client.get(
        url_for(
            "cms.publish",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 400

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "DRAFT"

    stub_measure_page.status = "INTERNAL_REVIEW"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.publish",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert mock_request_build.call_count == 0

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "INTERNAL_REVIEW"


def test_non_admin_user_can_not_publish_page_in_dept_review(
    app, db, db_session, test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    stub_measure_page.status = "DEPARTMENT_REVIEW"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.publish",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 403

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "DEPARTMENT_REVIEW"


def test_admin_user_can_unpublish_page(
    app,
    db,
    db_session,
    test_app_client,
    mock_admin_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page,
    mock_request_build,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    stub_measure_page.status = "APPROVED"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.unpublish_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    mock_request_build.assert_called_once()

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "UNPUBLISH"
    assert page.unpublished_by == mock_admin_user.email


def test_non_admin_user_can_not_unpublish_page(
    app,
    db,
    db_session,
    test_app_client,
    mock_rdu_user,
    stub_topic_page,
    stub_subtopic_page,
    stub_measure_page,
    mock_request_build,
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    stub_measure_page.status = "APPROVED"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.unpublish_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 403
    assert mock_request_build.call_count == 0

    page_service = PageService()
    page_service.init_app(app)
    page = page_service.get_page(stub_measure_page.guid)
    assert page.status == "APPROVED"


def test_admin_user_can_see_publish_unpublish_buttons_on_edit_page(
    app, db, db_session, test_app_client, mock_admin_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_admin_user.id

    stub_measure_page.status = "DEPARTMENT_REVIEW"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("a", class_="button")[-1].text.strip().lower() == "approve for publishing"

    stub_measure_page.status = "APPROVED"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("a", class_="button")[-1].text.strip().lower() == "unpublish"


def test_internal_user_can_not_see_publish_unpublish_buttons_on_edit_page(
    app, db, db_session, test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    stub_measure_page.status = "DEPARTMENT_REVIEW"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("a", class_="button")[-1].text.strip().lower() == "reject"

    stub_measure_page.status = "APPROVED"
    db.session.add(stub_measure_page)
    db.session.commit()

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("a", class_="button")[-1].text.strip().lower() == "edit / create new version"


def test_order_measures_in_subtopic(app, db, db_session, test_app_client, mock_rdu_user, stub_subtopic_page):
    ids = [0, 1, 2, 3, 4]
    reversed_ids = ids[::-1]
    for i in ids:
        stub_subtopic_page.children.append(Page(guid=str(i), version="1.0", position=i))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    assert stub_subtopic_page.children[0].guid == "0"
    assert stub_subtopic_page.children[1].guid == "1"
    assert stub_subtopic_page.children[2].guid == "2"
    assert stub_subtopic_page.children[3].guid == "3"
    assert stub_subtopic_page.children[4].guid == "4"

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    updates = []
    for position, id in enumerate(reversed_ids):
        updates.append({"position": position, "guid": str(id), "subtopic": stub_subtopic_page.guid})

    resp = test_app_client.post(
        url_for("cms.set_measure_order"), data=json.dumps({"positions": updates}), content_type="application/json"
    )

    assert resp.status_code == 200

    page_service = PageService()
    page_service.init_app(app)
    udpated_page = page_service.get_page(stub_subtopic_page.guid)

    assert udpated_page.children[0].guid == "4"
    assert udpated_page.children[1].guid == "3"
    assert udpated_page.children[2].guid == "2"
    assert udpated_page.children[3].guid == "1"
    assert udpated_page.children[4].guid == "0"


def test_reorder_measures_triggers_build(app, db, db_session, test_app_client, mock_rdu_user, stub_subtopic_page):
    ids = [0, 1]
    reversed_ids = ids[::-1]
    for i in ids:
        stub_subtopic_page.children.append(Page(guid=str(i), version="1.0", position=i))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    builds = Build.query.all()

    assert len(builds) == 0

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    updates = []
    for position, id in enumerate(reversed_ids):
        updates.append({"position": position, "guid": str(id), "subtopic": stub_subtopic_page.guid})

    resp = test_app_client.post(
        url_for("cms.set_measure_order"), data=json.dumps({"positions": updates}), content_type="application/json"
    )

    assert resp.status_code == 200

    builds = Build.query.all()

    assert len(builds) == 1


def test_order_measures_in_subtopic_sets_order_on_all_versions(
    app, db, db_session, test_app_client, mock_rdu_user, stub_subtopic_page
):

    stub_subtopic_page.children.append(Page(guid="0", version="1.0", position=0))
    stub_subtopic_page.children.append(Page(guid="0", version="1.1", position=0))
    stub_subtopic_page.children.append(Page(guid="0", version="2.0", position=0))
    stub_subtopic_page.children.append(Page(guid="1", version="1.0", position=0))
    stub_subtopic_page.children.append(Page(guid="1", version="2.0", position=0))

    db.session.add(stub_subtopic_page)
    db.session.commit()

    assert stub_subtopic_page.children[0].guid == "0"
    assert stub_subtopic_page.children[1].guid == "0"
    assert stub_subtopic_page.children[2].guid == "0"
    assert stub_subtopic_page.children[3].guid == "1"
    assert stub_subtopic_page.children[4].guid == "1"

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    updates = [
        {"position": 0, "guid": "1", "subtopic": stub_subtopic_page.guid},
        {"position": 1, "guid": "0", "subtopic": stub_subtopic_page.guid},
    ]

    resp = test_app_client.post(
        url_for("cms.set_measure_order"), data=json.dumps({"positions": updates}), content_type="application/json"
    )

    assert resp.status_code == 200

    page_service = PageService()
    page_service.init_app(app)
    udpated_page = page_service.get_page(stub_subtopic_page.guid)

    assert udpated_page.children[0].guid == "1"
    assert udpated_page.children[1].guid == "1"
    assert udpated_page.children[2].guid == "0"
    assert udpated_page.children[3].guid == "0"
    assert udpated_page.children[4].guid == "0"


def test_view_edit_measure_page(
    test_app_client, mock_rdu_user, stub_topic_page, stub_subtopic_page, stub_measure_page, stub_measure_data
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert page.h1.text.strip() == "Edit page"

    title = page.find("input", attrs={"id": "title"})
    assert title
    assert title.attrs.get("value") == "Test Measure Page"

    subtopic = page.find("select", attrs={"id": "subtopic"})
    assert subtopic
    assert subtopic.find("option", selected=True).attrs.get("value") == "subtopic_example"

    time_covered = page.find("input", attrs={"id": "time_covered"})
    assert time_covered
    assert time_covered.attrs.get("value") == "4 months"

    assert len(page.find_all("input", class_="country")) == 4

    # TODO lowest level of geography

    methodology_label = page.find("label", attrs={"for": "methodology"})
    methodology = page.find("textarea", attrs={"id": "methodology"})

    assert methodology_label.text.strip() == "Methodology"
    assert methodology.text == "how we measure unemployment"

    suppression_and_disclosure_label = page.find("label", attrs={"for": "suppression_and_disclosure"})
    suppression_and_disclosure = page.find("textarea", attrs={"id": "suppression_and_disclosure"})

    assert suppression_and_disclosure_label.text.strip() == "Suppression rules and disclosure control (optional)"
    assert suppression_and_disclosure.text == "Suppression rules and disclosure control"

    rounding_label = page.find("label", attrs={"for": "estimation"})
    rounding = page.find("textarea", attrs={"id": "estimation"})

    assert rounding_label.text.strip() == "Rounding (optional)"
    assert rounding.text == "X people are unemployed"

    # Data sources

    # TODO publisher/dept source

    sources = page.find("fieldset", class_="source")
    source_text_label = sources.find("label", attrs={"for": "source_text"})
    source_text_input = sources.find("input", attrs={"id": "source_text"})

    assert source_text_label.text.strip() == "Title of data source page"
    assert source_text_input.attrs.get("value") == "DWP Stats"

    source_url = sources.find("input", attrs={"id": "source_url"})
    assert source_url.attrs.get("value") == "http://dwp.gov.uk"

    published_date = page.find("input", attrs={"id": "published_date"})
    assert published_date
    assert published_date.attrs.get("value") == "15th May 2017"

    note_on_corrections_or_updates_label = sources.find("label", attrs={"for": "note_on_corrections_or_updates"})
    note_on_corrections_or_updates = sources.find("textarea", attrs={"id": "note_on_corrections_or_updates"})

    assert note_on_corrections_or_updates_label.text.strip() == "Note on corrections or updates (optional)"
    assert note_on_corrections_or_updates.text == "Note on corrections or updates"

    # TODO frequency of release

    data_source_purpose_label = sources.find("label", attrs={"for": "data_source_purpose"})
    data_source_purpose = sources.find("textarea", attrs={"id": "data_source_purpose"})

    assert data_source_purpose_label.text.strip() == "Purpose of data source"
    assert data_source_purpose.text == "Purpose of data source"

    contact_name = page.find("input", attrs={"id": "contact_name"})
    assert contact_name
    assert contact_name.attrs.get("value") == "Jane Doe"

    contact_email = page.find("input", attrs={"id": "contact_email"})
    assert contact_email
    assert contact_email.attrs.get("value") == "janedoe@example.com"

    contact_phone = page.find("input", attrs={"id": "contact_phone"})
    assert contact_phone
    assert contact_phone.attrs.get("value") == ""

    summary = page.find("textarea", attrs={"id": "summary"})
    assert summary
    assert summary.text == stub_measure_data["summary"]

    need_to_know = page.find("textarea", attrs={"id": "need_to_know"})
    assert need_to_know
    assert need_to_know.text == "Need to know this"

    measure_summary = page.find("textarea", attrs={"id": "measure_summary"})
    assert measure_summary
    assert measure_summary.text == "Unemployment measure summary"

    ethnicity_definition_summary = page.find("textarea", attrs={"id": "ethnicity_definition_summary"})
    assert ethnicity_definition_summary
    assert ethnicity_definition_summary.text == "This is a summary of ethnicity definitions"

    methodology = page.find("textarea", attrs={"id": "methodology"})
    assert methodology
    assert methodology.text == "how we measure unemployment"

    estimation = page.find("textarea", attrs={"id": "estimation"})
    assert estimation
    assert estimation.text == "X people are unemployed"

    related_publications = page.find("textarea", attrs={"id": "related_publications"})
    assert related_publications
    assert related_publications.text == "Related publications"

    qmi_url = page.find("input", attrs={"id": "qmi_url"})
    assert qmi_url
    assert qmi_url.attrs.get("value") == "http://www.quality-street.gov.uk"

    further_technical_information = page.find("textarea", attrs={"id": "further_technical_information"})
    assert further_technical_information
    assert further_technical_information.text == "Further technical information"


def test_dept_user_should_not_be_able_to_delete_upload_if_page_not_shared(
    db_session, test_app_client, stub_measure_page, mock_dept_user, mock_delete_upload
):
    upload = Upload(guid="test-download")
    stub_measure_page.uploads.append(upload)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.delete_upload",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
            upload_guid=upload.guid,
        )
    )

    assert resp.status_code == 403

    mock_delete_upload.assert_not_called()


def test_dept_user_should_not_be_able_to_edit_upload_if_page_not_shared(
    db_session, test_app_client, stub_measure_page, mock_dept_user, mock_edit_upload
):
    upload = Upload(guid="test-download", file_name="test-download.csv")
    stub_measure_page.uploads.append(upload)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.edit_upload",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
            upload_guid=upload.guid,
        )
    )

    assert resp.status_code == 403

    mock_edit_upload.assert_not_called()


def test_dept_user_should_not_be_able_to_delete_dimension_if_page_not_shared(
    db_session, test_app_client, stub_page_with_dimension, mock_dept_user
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_page_with_dimension.parent.parent.uri,
            subtopic_uri=stub_page_with_dimension.parent.uri,
            measure_uri=stub_page_with_dimension.uri,
            version=stub_page_with_dimension.version,
        )
    )

    assert resp.status_code == 403

    resp = test_app_client.get(
        url_for(
            "cms.delete_dimension",
            topic_uri=stub_page_with_dimension.parent.parent.uri,
            subtopic_uri=stub_page_with_dimension.parent.uri,
            measure_uri=stub_page_with_dimension.uri,
            version=stub_page_with_dimension.version,
            dimension_guid=stub_page_with_dimension.dimensions[0].guid,
        )
    )

    assert resp.status_code == 403


def test_dept_user_should_be_able_to_edit_shared_page(
    db_session, test_app_client, stub_measure_page, mock_logged_in_dept_user
):
    stub_measure_page.title = "this will be updated"
    stub_measure_page.shared_with.append(mock_logged_in_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    data = {"title": "this is the update", "db_version_id": stub_measure_page.db_version_id + 1}
    resp = test_app_client.post(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        data=data,
        follow_redirects=True,
    )

    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == 'Updated page "this is the update"'


def test_dept_user_should_be_able_to_send_shared_page_to_review(
    db_session, test_app_client, stub_measure_page, mock_dept_user
):
    stub_measure_page.title = "the page to review"
    stub_measure_page.shared_with.append(mock_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "cms.send_to_review",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="alert-box").span.string == 'Sent page "the page to review" to INTERNAL_REVIEW'


def test_dept_cannot_publish_a_shared_page(db_session, test_app_client, stub_measure_page, mock_dept_user):

    stub_measure_page.title = "try to publish"
    stub_measure_page.status = "DEPARTMENT_REVIEW"
    stub_measure_page.shared_with.append(mock_dept_user)
    db_session.session.add(stub_measure_page)
    db_session.session.commit()

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dept_user.id

    resp = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        )
    )

    assert resp.status_code == 200

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert not page.find("a", id="send-to-approved")

    resp = test_app_client.get(
        url_for(
            "cms.publish",
            topic_uri=stub_measure_page.parent.parent.uri,
            subtopic_uri=stub_measure_page.parent.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert resp.status_code == 403


@pytest.mark.parametrize(
    "mock_user, can_see_copy_button",
    [
        (TypeOfUser.DEPT_USER, False),
        (TypeOfUser.RDU_USER, False),
        (TypeOfUser.ADMIN_USER, False),
        (TypeOfUser.DEV_USER, True),
    ],
    indirect=["mock_user"],
)
def test_only_allowed_users_can_see_copy_measure_button_on_edit_page(
    test_app_client, stub_topic_page, stub_subtopic_page, stub_measure_page, mock_user, can_see_copy_button
):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_user.id

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    page_button_texts = [button.text.strip().lower() for button in page.find_all("button", class_="button")]
    assert ("create a copy of this measure" in page_button_texts) is can_see_copy_button


def test_copy_measure_page(test_app_client, mock_dev_user, stub_topic_page, stub_subtopic_page, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_dev_user.id

    resp = test_app_client.post(
        url_for(
            "cms.copy_measure_page",
            topic_uri=stub_topic_page.uri,
            subtopic_uri=stub_subtopic_page.uri,
            measure_uri=stub_measure_page.uri,
            version=stub_measure_page.version,
        ),
        follow_redirects=True,
    )

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

    assert page.find("h1").text == "Edit page"
    assert page.find("input", attrs={"name": "title"})["value"] == "COPY OF Test Measure Page"

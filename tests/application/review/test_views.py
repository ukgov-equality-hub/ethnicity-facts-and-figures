import pytest
import uuid

from bs4 import BeautifulSoup
from flask import url_for
from itsdangerous import SignatureExpired, BadSignature

from application.cms.models import Upload
from application.cms.page_service import page_service
from application.utils import decode_review_token


def test_review_link_returns_page(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    assert stub_measure_page.status == "DRAFT"
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    assert stub_measure_page.status == "DEPARTMENT_REVIEW"

    resp = test_app_client.get(url_for("review.review_page", review_token=stub_measure_page.review_token))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("h1").text.strip() == stub_measure_page.title


def test_review_link_returns_404_if_token_incomplete(test_app_client, mock_rdu_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session["user_id"] = mock_rdu_user.id

    assert stub_measure_page.status == "DRAFT"
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    assert stub_measure_page.status == "DEPARTMENT_REVIEW"

    broken_token = stub_measure_page.review_token.replace(".", " ")

    resp = test_app_client.get(url_for("review.review_page", review_token=broken_token))

    assert resp.status_code == 404

    broken_token = "this will not work"

    resp = test_app_client.get(url_for("review.review_page", review_token=broken_token))

    assert resp.status_code == 404


def test_review_token_decoded_if_not_expired(app, mock_rdu_user, stub_measure_page):

    assert stub_measure_page.status == "DRAFT"
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    assert stub_measure_page.status == "DEPARTMENT_REVIEW"

    expires_tomorrow = 1
    slug, version = decode_review_token(
        stub_measure_page.review_token,
        {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expires_tomorrow},
    )

    assert slug == stub_measure_page.slug
    assert version == stub_measure_page.version


def test_review_token_expired_throws_signature_expired(app, mock_rdu_user, stub_measure_page):

    assert stub_measure_page.status == "DRAFT"
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    assert stub_measure_page.status == "DEPARTMENT_REVIEW"

    expired_yesterday = -1

    with pytest.raises(SignatureExpired):
        decode_review_token(
            stub_measure_page.review_token,
            {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expired_yesterday},
        )


def test_review_token_messed_up_throws_bad_signature(app, mock_rdu_user, stub_measure_page):

    assert stub_measure_page.status == "DRAFT"
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    page_service.next_state(stub_measure_page, mock_rdu_user.email)
    assert stub_measure_page.status == "DEPARTMENT_REVIEW"

    broken_token = stub_measure_page.review_token.replace(".", " ")

    expires_tomorrow = 1

    with pytest.raises(BadSignature):
        decode_review_token(
            broken_token, {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expires_tomorrow}
        )

    broken_token = "this will not work"

    with pytest.raises(BadSignature):
        decode_review_token(
            broken_token, {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expires_tomorrow}
        )


def test_page_main_download_available_without_login(
    db_session, test_app_client, stub_measure_page, mock_get_measure_download, mock_get_csv_data_for_download
):
    upload = Upload(guid=str(uuid.uuid4()), title="test file", file_name="test-file.csv")
    stub_measure_page.uploads = [upload]

    db_session.session.commit()

    resp = test_app_client.get(
        url_for(
            "static_site.measure_page_file_download",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
            filename=stub_measure_page.uploads[0].file_name,
        )
    )

    mock_get_measure_download.assert_called_with(upload, upload.file_name, "source")
    mock_get_csv_data_for_download.assert_called_with(upload.file_name)

    assert resp.status_code == 200
    assert resp.content_type == "text/csv; charset=utf-8"
    assert resp.headers["Content-Disposition"] == "attachment; filename=%s" % upload.file_name


def test_page_dimension_download_available_without_login(test_app_client, mock_rdu_user, stub_page_with_dimension):

    resp = test_app_client.get(
        url_for(
            "static_site.dimension_file_download",
            topic_slug=stub_page_with_dimension.parent.parent.slug,
            subtopic_slug=stub_page_with_dimension.parent.slug,
            measure_slug=stub_page_with_dimension.slug,
            version=stub_page_with_dimension.version,
            dimension_guid=stub_page_with_dimension.dimensions[0].guid,
        )
    )

    assert resp.status_code == 200
    assert resp.content_type == "text/csv"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

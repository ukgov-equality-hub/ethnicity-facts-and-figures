import pytest

from bs4 import BeautifulSoup
from flask import url_for
from itsdangerous import SignatureExpired, BadSignature, URLSafeTimedSerializer

from application.utils import decode_review_token
from application.auth.models import TypeOfUser
from tests.models import MeasureVersionFactory, MeasureVersionWithDimensionFactory, UserFactory


def test_review_link_returns_page(test_app_client):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    resp = test_app_client.get(url_for("review.review_page", review_token=measure_version.review_token))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert page.find("h1").text.strip() == measure_version.title


def test_review_page_does_not_include_status_bar(test_app_client):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    resp = test_app_client.get(url_for("review.review_page", review_token=measure_version.review_token))

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert not page.find("div", class_="status")


def test_review_link_returns_404_if_token_incomplete(test_app_client):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    broken_token = measure_version.review_token.replace(".", " ")
    resp = test_app_client.get(url_for("review.review_page", review_token=broken_token))

    assert resp.status_code == 404

    broken_token = "this will not work"

    resp = test_app_client.get(url_for("review.review_page", review_token=broken_token))

    assert resp.status_code == 404


def test_review_token_decoded_if_not_expired(app):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")

    expires_tomorrow = 1
    decoded_guid, decoded_version = decode_review_token(
        measure_version.review_token,
        {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expires_tomorrow},
    )

    assert decoded_guid == str(measure_version.id)
    assert decoded_version is None


def test_old_style_review_token_decoded_if_not_expired(app):

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW", guid="test-measure-page")
    old_style_token = serializer.dumps(f"{measure_version.guid}|{measure_version.version}")
    measure_version.review_token = old_style_token

    expires_tomorrow = 1
    decoded_guid, decoded_version = decode_review_token(
        measure_version.review_token,
        {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expires_tomorrow},
    )

    assert decoded_guid == measure_version.guid
    assert decoded_version == measure_version.version


def test_review_token_expired_throws_signature_expired(app):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    expired_yesterday = -1

    with pytest.raises(SignatureExpired):
        decode_review_token(
            measure_version.review_token,
            {"SECRET_KEY": app.config["SECRET_KEY"], "PREVIEW_TOKEN_MAX_AGE_DAYS": expired_yesterday},
        )


def test_review_token_messed_up_throws_bad_signature(app):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")

    broken_token = measure_version.review_token.replace(".", " ")

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


@pytest.mark.parametrize("user_type", (TypeOfUser.RDU_USER, TypeOfUser.ADMIN_USER, TypeOfUser.DEV_USER))
def test_users_can_generate_new_review_tokens(test_app_client, user_type):
    user = UserFactory(user_type=user_type)

    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW", review_token=None, measure__shared_with=[])
    resp = test_app_client.get(url_for("review.get_new_review_url", id=measure_version.id))
    assert resp.status_code == 200
    assert measure_version.review_token is not None


def test_dept_users_can_only_generate_new_review_tokens_for_shared_measures(test_app_client, logged_in_dept_user):

    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW", review_token=None, measure__shared_with=[])
    # Measure is not shared with the user
    resp = test_app_client.get(url_for("review.get_new_review_url", id=measure_version.id))
    assert resp.status_code == 403
    assert measure_version.review_token is None

    # Once measure is shared the user can create a review token
    measure_version.measure.shared_with = [logged_in_dept_user]
    resp = test_app_client.get(url_for("review.get_new_review_url", id=measure_version.id))
    assert resp.status_code == 200
    assert measure_version.review_token is not None


def test_page_main_download_available_without_login(
    test_app_client, mock_get_measure_download, mock_get_csv_data_for_download
):
    measure_version = MeasureVersionFactory(
        status="DEPARTMENT_REVIEW", uploads__title="test file", uploads__file_name="test-file.csv"
    )

    resp = test_app_client.get(
        url_for(
            "static_site.measure_version_file_download",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            filename=measure_version.uploads[0].file_name,
        )
    )

    mock_get_measure_download.assert_called_with(measure_version.uploads[0], "test-file.csv", "source")
    mock_get_csv_data_for_download.assert_called_with("test-file.csv")

    assert resp.status_code == 200
    assert resp.content_type == "text/csv; charset=utf-8"
    assert resp.headers["Content-Disposition"] == "attachment; filename=test-file.csv"


def test_page_dimension_download_available_without_login(test_app_client):

    measure_version = MeasureVersionWithDimensionFactory(dimensions__title="stub dimension")

    resp = test_app_client.get(
        url_for(
            "static_site.dimension_file_download",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=measure_version.dimensions[0].guid,
        )
    )

    assert resp.status_code == 200
    assert resp.content_type == "text/csv"
    assert resp.headers["Content-Disposition"] == 'attachment; filename="stub-dimension.csv"'

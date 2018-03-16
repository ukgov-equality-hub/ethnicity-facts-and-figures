import pytest
from bs4 import BeautifulSoup
from flask import url_for
from itsdangerous import SignatureExpired, BadSignature

from application.cms.page_service import page_service
from application.utils import decode_review_token


def test_review_link_returns_page(test_app_client, mock_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    assert stub_measure_page.status == 'DRAFT'
    page_service.next_state(stub_measure_page, mock_user.email)
    page_service.next_state(stub_measure_page, mock_user.email)
    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    resp = test_app_client.get(url_for('review.review_page', review_token=stub_measure_page.review_token))

    assert resp.status_code == 200
    page = BeautifulSoup(resp.data.decode('utf-8'), 'html.parser')
    assert page.find('h1').text.strip() == stub_measure_page.title


def test_review_link_returns_404_if_token_incomplete(test_app_client, mock_user, stub_measure_page):

    with test_app_client.session_transaction() as session:
        session['user_id'] = mock_user.id

    assert stub_measure_page.status == 'DRAFT'
    page_service.next_state(stub_measure_page, mock_user.email)
    page_service.next_state(stub_measure_page, mock_user.email)
    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    broken_token = stub_measure_page.review_token.replace('.', ' ')

    resp = test_app_client.get(url_for('review.review_page', review_token=broken_token))

    assert resp.status_code == 404

    broken_token = 'this will not work'

    resp = test_app_client.get(url_for('review.review_page', review_token=broken_token))

    assert resp.status_code == 404


def test_review_token_decoded_if_not_expired(app, mock_user, stub_measure_page):

    assert stub_measure_page.status == 'DRAFT'
    page_service.next_state(stub_measure_page, mock_user.email)
    page_service.next_state(stub_measure_page, mock_user.email)
    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    expires_tomorrow = 1
    uri, version = decode_review_token(stub_measure_page.review_token, {'SECRET_KEY': app.config['SECRET_KEY'],
                                                                        'PREVIEW_TOKEN_MAX_AGE_DAYS': expires_tomorrow})

    assert uri == stub_measure_page.uri
    assert version == stub_measure_page.version


def test_review_token_expired_throws_signature_expired(app, mock_user, stub_measure_page):

    assert stub_measure_page.status == 'DRAFT'
    page_service.next_state(stub_measure_page, mock_user.email)
    page_service.next_state(stub_measure_page, mock_user.email)
    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    expired_yesterday = -1

    with pytest.raises(SignatureExpired):
        decode_review_token(stub_measure_page.review_token, {'SECRET_KEY': app.config['SECRET_KEY'],
                                                             'PREVIEW_TOKEN_MAX_AGE_DAYS': expired_yesterday})


def test_review_token_messed_up_throws_bad_signature(app, mock_user, stub_measure_page):

    assert stub_measure_page.status == 'DRAFT'
    page_service.next_state(stub_measure_page, mock_user.email)
    page_service.next_state(stub_measure_page, mock_user.email)
    assert stub_measure_page.status == 'DEPARTMENT_REVIEW'

    broken_token = stub_measure_page.review_token.replace('.', ' ')

    expires_tomorrow = 1

    with pytest.raises(BadSignature):
        decode_review_token(broken_token, {'SECRET_KEY': app.config['SECRET_KEY'],
                                           'PREVIEW_TOKEN_MAX_AGE_DAYS': expires_tomorrow})

    broken_token = 'this will not work'

    with pytest.raises(BadSignature):
        decode_review_token(broken_token, {'SECRET_KEY': app.config['SECRET_KEY'],
                                           'PREVIEW_TOKEN_MAX_AGE_DAYS': expires_tomorrow})

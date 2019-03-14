from bs4 import BeautifulSoup

from flask import url_for

from application.utils import generate_token
from application.auth.models import TypeOfUser

from tests.models import UserFactory


def test_confirm_account_rejects_easy_password(app, test_app_client):
    rdu_user = UserFactory(user_type=TypeOfUser.RDU_USER, active=False)

    token = generate_token(rdu_user.email, app)
    confirmation_url = url_for("register.confirm_account", token=token, _external=True)

    rdu_user.active = False

    user_details = {"password": "long-enough-but-too-easy", "confirm_password": "long-enough-but-too-easy"}
    resp = test_app_client.post(confirmation_url, data=user_details, follow_redirects=True)

    page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").text.strip()
        == "Your password is too weak. Use a mix of numbers as well as upper and lowercase letters"
    )

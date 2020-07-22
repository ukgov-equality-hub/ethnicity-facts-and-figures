from tests.functional.pages import HomePage
from application.auth.models import TypeOfUser
from tests.functional.utils import driver_login
from tests.models import UserFactory


def test_can_search_from_homepage_with_javascript(driver, live_server):

    admin_user = UserFactory(user_type=TypeOfUser.ADMIN_USER, active=True)
    driver_login(driver, live_server, admin_user)

    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()

    home_page.search_site("health")

from pytest_bdd import scenario, given, when, then


@scenario('features/edit_measure_pages.feature', 'Lifecycle of a measure page')
def test_edit_measure_pages():
    pass


@given("I'm a signed in user")
def get_user():
    print("signing in a user")


@when('I create a new page')
def create_new_page():
    print("create new page")


@then('a new page should exist')
def page_should_exist():
    print("page should exist")

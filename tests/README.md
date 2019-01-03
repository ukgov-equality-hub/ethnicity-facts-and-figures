# Tests

This directory contains tests that cover the code for the Race Disparity Unit's “Ethnicity Facts and Figures” service. Our unit tests are found in `tests/application/` and mirror the structure of the top-level `application/` module. Our end-to-end tests are more free-form and found under `tests/functional/`.

# How our tests work

We make liberal use of [pytest fixtures](https://docs.pytest.org/en/latest/fixture.html) to minimise the amount of boilerplate setup code we need to write for each test. These are found in `conftest.py` files.

Some of our fixtures are applied automatically to all tests. Important examples are:

* A full database migration runs at the start of each test session [see `conftest:db_migration`].
* Before **every** test, all records from the database are removed (EXCEPT materialized views, which need to be refreshed on an as-needed basis within the test that needs them) [see `conftest:db_session`].
* All network requests via the `requests` library are mocked out to raise exceptions, with the aim of preventing (most) requests from reaching out to the Internet [see `conftest:requests_mocker`]

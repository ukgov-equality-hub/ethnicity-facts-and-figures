from lxml import html
from application.cms.models import MeasureVersion


class GeneralTestException(Exception):
    pass


class UnmockedRequestException(GeneralTestException):
    pass


class UnexpectedMockInvocationException(GeneralTestException):
    pass


def get_page_with_title(title):
    return MeasureVersion.query.filter_by(title=title).one()


def assert_strings_match_ignoring_whitespace(string_1, string_2):
    assert "".join(string_1.split()) == "".join(string_2.split())


def page_displays_error_matching_message(response, message: str) -> bool:
    doc = html.fromstring(response.get_data(as_text=True))

    error_summary = doc.xpath(
        "//div[contains(@class, 'govuk-error-summary')]//a[normalize-space(text())=$message]", message=message
    )

    return True if error_summary else False

from application.cms.models import MeasureVersion


class GeneralTestException(Exception):
    pass


class UnmockedRequestException(GeneralTestException):
    pass


class UnexpectedMockInvocationException(GeneralTestException):
    pass


def get_page_with_title(title):
    return MeasureVersion.query.filter_by(title=title).one()

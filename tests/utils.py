from application.cms.models import Page


class GeneralTestException(Exception):
    pass


class UnmockedRequestException(GeneralTestException):
    pass


class UnexpectedMockInvocationException(GeneralTestException):
    pass


def create_measure_page_versions(db, example_measure_page, required_versions):
    for page_version in required_versions:
        page = Page(
            guid="test",
            version=page_version,
            parent_guid=example_measure_page.parent.guid,
            parent_version=example_measure_page.parent.version,
            page_type="measure",
            uri="test-measure-page-2",
            title="Test measure page 2",
            status="APPROVED",
        )
        db.session.add(page)

    db.session.commit()

from application.cms.models import MeasureVersion


class GeneralTestException(Exception):
    pass


class UnmockedRequestException(GeneralTestException):
    pass


class UnexpectedMockInvocationException(GeneralTestException):
    pass


def create_measure_versions(db, example_measure_page, required_versions, required_titles=None, parent_measure=None):
    if not required_titles:
        required_titles = [f"Test {version}" for version in required_versions]

    for page_version, page_title in zip(required_versions, required_titles):
        measure_version = MeasureVersion(
            guid="test",
            version=page_version,
            parent_guid=example_measure_page.parent.guid,
            parent_version=example_measure_page.parent.version,
            page_type="measure",
            slug="test-measure-page-2",
            title=page_title,
            status="APPROVED",
        )
        if parent_measure:
            measure_version.measure = parent_measure
        db.session.add(measure_version)

    db.session.commit()

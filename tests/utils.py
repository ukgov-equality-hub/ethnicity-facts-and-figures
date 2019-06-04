from lxml import html
from werkzeug.datastructures import ImmutableMultiDict

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


def multidict_from_measure_version_and_kwargs(measure_version: MeasureVersion, **kwargs) -> ImmutableMultiDict:
    return ImmutableMultiDict(
        {
            "title": measure_version.title,
            "description": measure_version.description,
            "measure_summary": measure_version.measure_summary,
            "summary": measure_version.summary,
            "lowest_level_of_geography": measure_version.lowest_level_of_geography_id,
            "area_covered": [area_covered.name for area_covered in measure_version.area_covered],
            "time_covered": measure_version.time_covered,
            "need_to_know": measure_version.need_to_know,
            "ethnicity_definition_summary": measure_version.ethnicity_definition_summary,
            "related_publications": measure_version.related_publications,
            "methodology": measure_version.methodology,
            "suppression_and_disclosure": measure_version.suppression_and_disclosure,
            "estimation": measure_version.estimation,
            "qmi_url": measure_version.qmi_url,
            "further_technical_information": measure_version.further_technical_information,
            "db_version_id": measure_version.db_version_id,
            **kwargs,
        }
    )


def details_tag_with_summary(dom_node, summary_text):

    summary_tags = dom_node.find_all("summary")

    summary_tags_with_matching_text = list(filter(lambda x: x.get_text().strip() == summary_text, summary_tags))

    if len(summary_tags_with_matching_text) > 0:
        return summary_tags_with_matching_text[0].parent
    else:
        return None


def find_link_with_text(dom_node, link_text):

    return dom_node.find("a", string=link_text)

import os

from application.utils import get_content_with_metadata


def test_metadata_contains_all_required_data(stub_measure_page):
    directory = os.path.abspath(os.path.dirname(__file__))
    test_file = os.path.join(directory, 'test_data/dummy_data.csv')

    output = get_content_with_metadata(test_file, stub_measure_page)

    lines = output.split('\n')

    assert lines[0] == '"Title","%s"' % stub_measure_page.title
    assert lines[1] == '"Location","%s"' % stub_measure_page.format_area_covered()
    assert lines[2] == '"Time period","%s"' % stub_measure_page.time_covered
    assert lines[3] == '"Data source","%s"' % stub_measure_page.department_source.name
    assert lines[4] == '"Data source link","%s"' % stub_measure_page.source_url
    # skip line 5 as value comes from environment variable
    assert lines[6] == '"Last updated","%s"' % stub_measure_page.publication_date

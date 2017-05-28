import pytest

from application.cms.data_utils import Autogenerator


def test_chart_processor_generates_table_for_simple_chart_object(stub_measure_page, stub_simple_chart_object):

    page = stub_measure_page
    page.dimensions[0].chart = stub_simple_chart_object

    Autogenerator().autogenerate(page=page)

    assert page.dimensions[0].table != ''
    assert page.dimensions[0].table['type'] == 'simple'


def test_chart_processor_generates_table_for_grouped_chart_object(stub_measure_page, stub_grouped_chart_object):

    page = stub_measure_page
    page.dimensions[0].chart = stub_grouped_chart_object

    Autogenerator().autogenerate(page=page)

    assert page.dimensions[0].table != ''
    assert page.dimensions[0].table['type'] == 'grouped'


def test_chart_processor_generates_row_by_row_table_for_line_graph_object(stub_measure_page, stub_line_graph_object):
    # given a page with a line graph (with a large number of ethnicities and time periods)
    page = stub_measure_page
    page.dimensions[0].chart = stub_line_graph_object

    # when we autogenerate
    Autogenerator().autogenerate(page=page)

    # a table object is generated with Ethnicity for category and Time as first field of the individual items
    table = page.dimensions[0].table
    chart = page.dimensions[0].chart

    chart_times = chart['xAxis']['categories']
    chart_ethnicities = [s['name'] for s in chart['series']]
    assert 'Black' in chart_ethnicities
    assert '2015' in chart_times

    row = table['data'][0]
    assert table['type'] == 'simple'
    assert table['category'] == 'Ethnicity'

    # get a data point
    assert row['category'] in chart_ethnicities
    assert row['values'][0] in chart_times


def test_chart_processor_generates_years_for_columns_where_years_small(stub_measure_page,
                                                                       stub_short_time_line_graph_object):
    # given a page with a line graph (with fewer than 6 time periods)
    page = stub_measure_page
    page.dimensions[0].chart = stub_short_time_line_graph_object

    # when we autogenerate
    Autogenerator().autogenerate(page=page)

    # a grouped table object is generated with Ethnicity for group title and Time as the individual items
    table = page.dimensions[0].table
    chart = page.dimensions[0].chart

    chart_times = chart['xAxis']['categories']
    chart_ethnicities = [s['name'] for s in chart['series']]
    assert 'Black' in chart_ethnicities
    assert '2015' in chart_times

    assert table['type'] == 'grouped'
    group = table['groups'][0]
    assert group['group'] in chart_ethnicities

    item = group['data'][0]
    assert item['category'] in chart_times


def test_chart_processor_generates_ethnicities_for_columns_where_years_large_ethnicities_small(
        stub_measure_page, stub_small_ethnicities_line_graph_object):
    # given a page with a line graph (with fewer than 6 time periods)
    page = stub_measure_page
    page.dimensions[0].chart = stub_small_ethnicities_line_graph_object

    # when we autogenerate
    Autogenerator().autogenerate(page=page)

    # a grouped table object is generated with Ethnicity for group title and Time as the individual items
    table = page.dimensions[0].table
    chart = page.dimensions[0].chart

    chart_times = chart['xAxis']['categories']
    chart_ethnicities = [s['name'] for s in chart['series']]
    assert 'Black' in chart_ethnicities
    assert '2015' in chart_times

    assert table['type'] == 'grouped'
    group = table['groups'][0]
    assert group['group'] in chart_times

    item = group['data'][0]
    assert item['category'] in chart_ethnicities


def test_chart_processor_generates_table_for_component_chart(
        stub_measure_page, stub_component_chart_object):
    # given a page with a line graph (with fewer than 6 time periods)
    page = stub_measure_page
    page.dimensions[0].chart = stub_component_chart_object

    # when we autogenerate
    Autogenerator().autogenerate(page=page)

    # a grouped table object is generated with Ethnicity for group title and the components as the individual items
    table = page.dimensions[0].table
    chart = page.dimensions[0].chart

    chart_ethnicities = chart['xAxis']['categories']
    chart_components = [s['name'] for s in chart['series']]
    assert 'Black African' in chart_ethnicities
    assert 'Female' in chart_components

    assert table['type'] == 'grouped'
    group = table['groups'][0]
    assert group['group'] in chart_ethnicities

    item = group['data'][0]
    assert item['category'] in chart_components

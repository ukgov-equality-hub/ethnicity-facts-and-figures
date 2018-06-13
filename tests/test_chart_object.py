"""
ChartObjectDataBuilder

upgrade_v1_to_v2 should upgrade dimension values with chart_1 dict and chart_1_settings dict to chart_2_settings

"""

from application.cms.data_utils import ChartObjectDataBuilder


def test_upgrade_does_copy_chart_type():
    # GIVEN
    value = 'blah'

    # WHEN
    upgraded = ChartObjectDataBuilder.get_v2_chart_type({'type': value})

    # THEN
    assert upgraded['type'] == value


def test_upgrade_does_convert_bar_chart_with_second_dimension():
    # GIVEN
    from tests.test_data.chart_convert import bar, bar_source, bar_grouped, bar_grouped_source

    # WHEN
    upgraded_simple = ChartObjectDataBuilder.upgrade_v1_to_v2(bar, bar_source)
    upgraded_grouped = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped, bar_grouped_source)

    # THEN
    assert upgraded_simple['type'] == 'bar_chart'
    assert upgraded_grouped['type'] == 'grouped_bar_chart'


'''
BAR CHART FUNCTIONALITY
'''


def test_bar_chart_has_data_points_ethnicity_value():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar, bar_source

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar, bar_source)

    # THEN
    #
    assert 'data' in upgraded_bar
    assert upgraded_bar['data'][0] == ['Ethnicity', 'Value']


def test_bar_chart_takes_data_points_from_chart_object():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar, bar_source

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar, bar_source)

    # THEN
    #
    assert upgraded_bar['data'][1] == ['White', 71.12375533]


'''
LINE GRAPH FUNCTIONALITY
'''


def test_line_graph_has_x_axis_set():
    # GIVEN
    #
    from tests.test_data.chart_convert import line, line_source

    # WHEN
    #
    upgraded_line = ChartObjectDataBuilder.upgrade_v1_to_v2(line, line_source)

    # THEN
    #
    assert 'chartOptions' in upgraded_line
    assert 'x_axis_column' in upgraded_line['chartOptions']
    assert upgraded_line['chartOptions']['x_axis_column'] == 'Time'


def test_line_graph_has_data_points_ethnicity_x_axis_value():
    # GIVEN
    #
    from tests.test_data.chart_convert import line, line_source

    # WHEN
    #
    upgraded_line = ChartObjectDataBuilder.upgrade_v1_to_v2(line, line_source)

    # THEN
    #
    assert 'data' in upgraded_line
    assert upgraded_line['data'][0] == ['Ethnicity', 'Time', 'Value']


def test_line_graph_takes_data_points_from_chart():
    # GIVEN
    #
    from tests.test_data.chart_convert import line, line_source

    # WHEN
    #
    upgraded_line = ChartObjectDataBuilder.upgrade_v1_to_v2(line, line_source)

    # THEN
    #
    assert upgraded_line['data'][1] == ['All', '2005/06', 70]


'''
GROUPED BAR FUNCTIONALITY
'''


def test_grouped_bar_chart_has_data_type_set():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar_grouped, bar_grouped_source

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped, bar_grouped_source)

    # THEN
    #
    assert 'chartOptions' in upgraded_bar
    assert 'data_style' in upgraded_bar['chartOptions']


def test_grouped_bar_chart_has_ethnicity_as_groups_if_categories_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar_grouped_2, bar_grouped_source_2

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped_2, bar_grouped_source_2)

    # THEN
    #
    assert upgraded_bar['chartOptions']['data_style'] == 'ethnicity_as_group'


def test_grouped_bar_chart_takes_data_points_from_chart_if_categories_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar_grouped_2, bar_grouped_source_2

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped_2, bar_grouped_source_2)

    # THEN
    #
    assert upgraded_bar['data'][1] == ['Asian', 'Boys', 73]


def test_grouped_bar_chart_has_ethnicity_as_bars_if_series_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar_grouped, bar_grouped_source

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped, bar_grouped_source)

    # THEN
    #
    assert upgraded_bar['chartOptions']['data_style'] == 'ethnicity_as_bar'


def test_grouped_bar_chart_takes_data_points_from_chart_if_series_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import bar_grouped, bar_grouped_source

    # WHEN
    #
    upgraded_bar = ChartObjectDataBuilder.upgrade_v1_to_v2(bar_grouped, bar_grouped_source)

    # THEN
    #
    assert upgraded_bar['data'][1] == ['White British', 'Higher managerial', 82]


'''
COMPONENT CHART FUNCTIONALITY
'''


def test_component_bar_chart_has_data_type_set():
    # GIVEN
    #
    from tests.test_data.chart_convert import component_ethnicity_bars, component_ethnicity_bars_source

    # WHEN
    #
    upgraded_component = ChartObjectDataBuilder.upgrade_v1_to_v2(component_ethnicity_bars,
                                                                 component_ethnicity_bars_source)

    # THEN
    #
    assert 'chartOptions' in upgraded_component
    assert 'data_style' in upgraded_component['chartOptions']


def test_component_chart_has_ethnicity_as_groups_if_bars_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import component_ethnicity_bars, component_ethnicity_bars_source

    # WHEN
    #
    upgraded_component = ChartObjectDataBuilder.upgrade_v1_to_v2(component_ethnicity_bars,
                                                                 component_ethnicity_bars_source)

    # THEN
    #
    assert upgraded_component['chartOptions']['data_style'] == 'ethnicity_as_bar'


def test_component_bar_chart_takes_data_points_from_chart_if_bars_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import component_ethnicity_bars, component_ethnicity_bars_source

    # WHEN
    #
    upgraded_component = ChartObjectDataBuilder.upgrade_v1_to_v2(component_ethnicity_bars,
                                                                 component_ethnicity_bars_source)

    # THEN
    #
    assert upgraded_component['data'][1] == ['All', '1,000 or more', 24]


def test_component_chart_has_ethnicity_as_bars_if_series_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import component_ethnicity_components, component_ethnicity_components_source

    # WHEN
    #
    upgraded_component = ChartObjectDataBuilder.upgrade_v1_to_v2(component_ethnicity_components,
                                                           component_ethnicity_components_source)

    # THEN
    #
    assert upgraded_component['chartOptions']['data_style'] == 'ethnicity_as_component'


def test_component_chart_takes_data_points_from_chart_if_series_are_ethnicity():
    # GIVEN
    #
    from tests.test_data.chart_convert import component_ethnicity_components, component_ethnicity_components_source

    # WHEN
    #
    upgraded_component = ChartObjectDataBuilder.upgrade_v1_to_v2(component_ethnicity_components,
                                                           component_ethnicity_components_source)

    # THEN
    #
    assert upgraded_component['data'][1] == ['Other', 'All', 18]

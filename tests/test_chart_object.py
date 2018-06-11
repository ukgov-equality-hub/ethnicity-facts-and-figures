"""
ChartObjectDataBuilder

upgrade_v1_to_v2 should upgrade dimension values with chart_1 dict and chart_1_settings dict to chart_2_settings

"""

from application.cms.data_utils import ChartObjectDataBuilder


def test_upgrade_does_copy_chart_type():
    # GIVEN
    value = 'blah'

    # WHEN
    upgraded = ChartObjectDataBuilder.upgrade_v1_to_v2(None, {'type': value})

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

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

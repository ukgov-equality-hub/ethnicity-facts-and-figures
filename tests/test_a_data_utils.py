import pytest


def test_stub_chart_object(stub_chart_object):
    assert stub_chart_object['type'] == 'bar'

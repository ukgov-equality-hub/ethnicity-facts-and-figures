import pytest

from application.cms.data_utils import Harmoniser


def test_harmoniser_appends_columns_to_data():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data
    data = [['a', 'any ethnicity type']]

    # when we add_columns
    harmoniser.harmonise(data=data)

    # then 4 columns are appended to the data
    assert data[0].__len__() == 6


def test_harmoniser_appends_columns_using_specific_ethnicity_type_in_lookup():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity type in the lookup
    data = [['a', 'phonetic'], ['b', 'phonetic']]

    # when we add_columns
    harmoniser.harmonise(data=data)

    # then added values come from entries in the lookup with ethnicity_type = ''
    assert data[0][2] == 'alpha'
    assert data[1][2] == 'bravo'


def test_harmoniser_appends_columns_using_defaults_for_unknown_ethnicity_type():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity type not in the lookup
    data = [['a', 'any ethnicity type'], ['b', 'any ethnicity type']]

    # when we add_columns
    harmoniser.harmonise(data=data)

    # the lookup falls back to ethnicity_type = ''
    assert data[0][2] == 'A'
    assert data[1][2] == 'B'


def test_harmoniser_appends_columns_using_own_values_where_no_match_found():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity entirely unlisted
    data = [['foo', 'ethnicity type bah']]

    # when we add_columns
    harmoniser.harmonise(data=data)

    # the lookup falls back to ethnicity_type = ''
    assert data[0][2] == 'foo'
    assert data[0][3] == 'foo'
    assert data[0][4] == ''
    assert data[0][5] == harmoniser.default_sort_value

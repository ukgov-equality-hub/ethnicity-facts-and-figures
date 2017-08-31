import pytest
import json
from flask import url_for

from application.cms.data_utils import Harmoniser


#
# These tests use a default lookup file.
#
# tests/test_data/test_lookups/test_lookup.csv
#

def test_harmoniser_appends_columns_to_data():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data
    data = [['a', 'any ethnicity type']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # then 4 columns are appended to the data
    assert data[0].__len__() == 6


def test_harmoniser_appends_columns_using_specific_ethnicity_type_in_lookup():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity type in the lookup
    data = [['a', 'phonetic'], ['b', 'phonetic']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # then added values come from entries in the lookup with ethnicity_type = ''
    assert data[0][2] == 'alpha'
    assert data[1][2] == 'bravo'


def test_harmoniser_appends_columns_using_case_insensitive_lookup():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data where one is capitalised
    data = [['A', 'phonetic'], ['b', 'phonetic']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # then values are added
    assert data[0][2] == 'alpha'
    assert data[1][2] == 'bravo'


def test_harmoniser_appends_columns_trimming_white_space_for_lookup():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data where one has forward white space and the other has trailing
    data = [[' A', 'phonetic'], ['b ', 'phonetic']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # then values are added
    assert data[0][2] == 'alpha'
    assert data[1][2] == 'bravo'


def test_harmoniser_appends_columns_using_defaults_for_unknown_ethnicity_type():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity type not in the lookup
    data = [['a', 'any ethnicity type'], ['b', 'any ethnicity type']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # the lookup falls back to ethnicity_type = ''
    assert data[0][2] == 'A'
    assert data[1][2] == 'B'


def test_harmoniser_can_handle_empty_rows():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given a dataset with a blank row
    data = [['a', 'any ethnicity type'], []]

    # when we add_columns
    try:
        harmoniser.append_columns(data=data)
    except IndexError:
        assert False


def test_harmoniser_without_default_values_appends_blanks_when_not_found():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given a dataset with a strange value
    data = [['strange', 'missing']]

    # when we add_columns
    harmoniser.append_columns(data)

    # then the extra values are appended
    assert data[0].__len__() == 6
    assert data[0][2] == ''
    assert data[0][3] == ''
    assert data[0][4] == ''
    assert data[0][5] == ''


def test_harmoniser_with_default_values_appends_defaults_when_not_found():
    default_values = ['one', 'two', 'three', 'four']
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv', default_values=default_values)

    # given a dataset with a strange value
    data = [['strange', 'missing']]

    # when we add_columns
    harmoniser.append_columns(data)

    # then the extra values are appended
    assert data[0].__len__() == 6
    assert data[0][2] == 'one'
    assert data[0][3] == 'two'
    assert data[0][4] == 'three'
    assert data[0][5] == 'four'


def test_harmoniser_with_wildcard_values_inserts_custom_defaults_when_not_found():
    default_values = ['*', 'two', 'Unknown - *', 'four']
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv', default_values=default_values)

    # given a dataset with a strange value
    data = [['strange', 'missing']]

    # when we add_columns
    harmoniser.append_columns(data)

    # then the extra values are appended
    assert data[0].__len__() == 6
    assert data[0][2] == 'strange'
    assert data[0][3] == 'two'
    assert data[0][4] == 'Unknown - strange'
    assert data[0][5] == 'four'


def test_processor_endpoint_responds(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)

    response = test_app_client.post(url_for('cms.process_input_data'),
                                    data=json.dumps({'data': [["Ethnicity", "Ethnicity_type", "Value"]]}),
                                    content_type='application/json',
                                    follow_redirects=True)

    assert response is not None


def test_processor_endpoint_looks_up_columns(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)

    # given a simple data set
    data = [["Ethnicity", "Ethnicity_type", "Value"],
            ["a", "phonetic", "12"]]

    # when we call the
    response = test_app_client.post(url_for('cms.process_input_data'),
                                    data=json.dumps({'data': data}),
                                    content_type='application/json',
                                    follow_redirects=True)
    data = json.loads(response.data.decode('utf-8'))

    row = data['data'][1]
    assert row[3] == 'alpha'
    assert row[4] == ''
    assert row[5] == ''
    assert row[6] == 100


def test_processor_endpoint_appends_default_values(test_app_client, test_app_editor):

    # Note: default values for the test_app are ['*','*','Unclassified',960]
    signin(test_app_editor, test_app_client)

    # given a simple data set
    data = [["Ethnicity", "Ethnicity_type", "Value"],
            ["strange", "", "12"]]

    # when we call the
    response = test_app_client.post(url_for('cms.process_input_data'),
                                    data=json.dumps({'data': data}),
                                    content_type='application/json',
                                    follow_redirects=True)
    data = json.loads(response.data.decode('utf-8'))

    row = data['data'][1]
    assert row[3] == 'strange'
    assert row[4] == 'strange'
    assert row[5] == 'Unclassified'
    assert row[6] == 960


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id

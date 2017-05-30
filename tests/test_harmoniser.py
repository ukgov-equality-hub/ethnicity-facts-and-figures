import pytest
import json
from flask import url_for

from application.cms.data_utils import Harmoniser


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


def test_harmoniser_appends_columns_using_defaults_for_unknown_ethnicity_type():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity type not in the lookup
    data = [['a', 'any ethnicity type'], ['b', 'any ethnicity type']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # the lookup falls back to ethnicity_type = ''
    assert data[0][2] == 'A'
    assert data[1][2] == 'B'


def test_harmoniser_appends_columns_using_own_values_where_no_match_found():
    harmoniser = Harmoniser('tests/test_data/test_lookups/test_lookup.csv')

    # given data from an ethnicity entirely unlisted
    data = [['foo', 'ethnicity type bah']]

    # when we add_columns
    harmoniser.append_columns(data=data)

    # the lookup falls back to ethnicity_type = ''
    assert data[0][2] == 'foo'
    assert data[0][3] == 'foo'
    assert data[0][4] == ''
    assert data[0][5] == harmoniser.default_sort_value


def test_processor_endpoint_responds(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)

    response = test_app_client.post(url_for('cms.process_input_data'),
                                    data=json.dumps({'data': [["Ethnicity", "Ethnicity_type", "Value"]]}),
                                    content_type='application/json',
                                    follow_redirects=True)

    assert response is not None


def test_processor_endpoint_returns_appropriate_headers(test_app_client, test_app_editor):
    signin(test_app_editor, test_app_client)

    # given a simple data set
    data = [["Ethnicity", "Ethnicity_type", "Value"],
            ["a", "phonetic", 12]]

    # when we call the
    response = test_app_client.post(url_for('cms.process_input_data'),
                                    data=json.dumps({'data': data}),
                                    content_type='application/json',
                                    follow_redirects=True)

    data = json.loads(response.data.decode('utf-8'))

    headers = data[0]
    assert headers[3] == 'Ethnicity-1'
    assert headers[4] == 'Ethnicity-2' 'Parent', 'Order'
    assert headers[5] == 'Parent'
    assert headers[6] == 'Order'


def test_processor_endpoint_returns_appropriate_headers(test_app_client, test_app_editor):
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

    headers = data['data'][0]
    assert headers[3] == 'Ethnicity-1'
    assert headers[4] == 'Ethnicity-2'
    assert headers[5] == 'Parent'
    assert headers[6] == 'Order'


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


def signin(user, to_client):
    with to_client.session_transaction() as session:
        session['user_id'] = user.id

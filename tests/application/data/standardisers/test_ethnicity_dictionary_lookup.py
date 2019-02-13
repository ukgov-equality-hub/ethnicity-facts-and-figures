import json
import random
from flask import url_for

from application.data.ethnicity_data_set import EthnicityDataset
from application.data.standardisers.ethnicity_dictionary_lookup import EthnicityDictionaryLookup


#
# These tests use a default lookup file.
#
# tests/test_data/test_lookups/test_lookup.csv
#
# the lookup maps ethnicities a, b, c, d
#
# default -> 'A', 'B', 'C', 'D'
# phonetic -> 'alpha', 'bravo', 'charlie', 'delta'


def test_dictionary_lookup_standardiser_appends_columns_to_data():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given data
    data_set = EthnicityDataset(data=[["Ethnicity", "Ethnicity type"], ["a", "any ethnicity type"]])

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then 4 columns are appended to the data
    assert 6 == data_set.get_data()[0].__len__()


def test_dictionary_lookup_standardiser_appends_columns_using_specific_ethnicity_type_in_lookup():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given data from an ethnicity type in the lookup
    data = [["Ethnicity", "Ethnicity type"], ["a", "phonetic"], ["b", "phonetic"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then added values come from entries in the lookup with ethnicity_type = ''
    assert data_set.get_data()[0][2] == "Label"
    assert data_set.get_data()[1][2] == "alpha"
    assert data_set.get_data()[2][2] == "bravo"


def test_dictionary_lookup_standardiser_appends_columns_using_case_insensitive_lookup():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given data where one is capitalised
    data = [["Ethnicity", "Ethnicity type"], ["A", "phonetic"], ["b", "phonetic"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then values are added
    assert data_set.get_data()[0][2] == "Label"
    assert data_set.get_data()[1][2] == "alpha"
    assert data_set.get_data()[2][2] == "bravo"


def test_dictionary_lookup_standardiser_appends_columns_trimming_white_space_for_lookup():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given data where one has forward white space and the other has trailing
    data = [["Ethnicity", "Ethnicity type"], [" a", "phonetic"], ["b ", "phonetic"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then values are added
    assert data_set.get_data()[0][2] == "Label"
    assert data_set.get_data()[1][2] == "alpha"
    assert data_set.get_data()[2][2] == "bravo"


def test_dictionary_lookup_standardiser_appends_columns_using_defaults_for_unknown_ethnicity_type():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given data from an ethnicity type not in the lookup
    data = [["Ethnicity", "Ethnicity type"], [" a", "xxx"], ["b ", "xxx"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then values are added
    assert data_set.get_data()[0][2] == "Label"
    assert data_set.get_data()[1][2] == "A"
    assert data_set.get_data()[2][2] == "B"


def test_dictionary_lookup_standardiser_can_handle_empty_rows():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given a dataset with a blank row
    data = [["Ethnicity", "Ethnicity type"], [" a", "xxx"], []]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    try:
        standardiser.process_data_set(data_set)
    except IndexError:
        assert False


def test_dictionary_lookup_standardiser_without_default_values_appends_blanks_when_not_found():
    standardiser = EthnicityDictionaryLookup("tests/test_data/test_dictionary_lookup/test_lookup.csv")

    # given a dataset with a strange value
    data = [["Ethnicity", "Ethnicity type"], ["strange", "missing"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then 4 blank values are appended for the four columns
    assert data_set.get_data()[1] == ["strange", "missing", "", "", "", ""]


def test_dictionary_lookup_standardiser_with_default_values_appends_defaults_when_not_found():
    default_values = ["one", "two", "three", "four"]
    standardiser = EthnicityDictionaryLookup(
        "tests/test_data/test_dictionary_lookup/test_lookup.csv", default_values=default_values
    )

    # given a dataset with a strange value
    data = [["Ethnicity", "Ethnicity type"], ["strange", "missing"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then the default values are appended for the four columns
    assert data_set.get_data()[1] == ["strange", "missing", "one", "two", "three", "four"]


def test_dictionary_lookup_standardiser_with_wildcard_values_inserts_custom_defaults_when_not_found():
    default_values = ["*", "two", "Unknown - *", "four"]
    standardiser = EthnicityDictionaryLookup(
        "tests/test_data/test_dictionary_lookup/test_lookup.csv", default_values=default_values
    )

    # given a dataset with a strange value
    data = [["Ethnicity", "Ethnicity type"], ["strange", "missing"]]
    data_set = EthnicityDataset(data=data)

    # when we add_columns
    standardiser.process_data_set(data_set)

    # then the default values are appended with * substituted with the ethnicity value
    assert data_set.get_data()[1] == ["strange", "missing", "strange", "two", "Unknown - strange", "four"]


def get_random_data(ethnicities, size):
    data = [[random.choice(ethnicities), "", "1"] for x in range(size)]
    data.insert(0, ["Ethnicity", "Ethnicity_type", "Value"])
    return data


def test_processor_endpoint_responds(test_app_client, logged_in_rdu_user):

    response = test_app_client.post(
        url_for("cms.process_input_data"),
        data=json.dumps({"data": [["Ethnicity", "Ethnicity_type", "Value"]]}),
        content_type="application/json",
        follow_redirects=True,
    )

    assert response is not None


def test_processor_endpoint_looks_up_columns(test_app_client, logged_in_rdu_user):

    # given a simple data set
    data = [["Ethnicity", "Ethnicity_type", "Value"], ["a", "phonetic", "12"]]

    # when we call the
    response = test_app_client.post(
        url_for("cms.process_input_data"),
        data=json.dumps({"data": data}),
        content_type="application/json",
        follow_redirects=True,
    )
    data = json.loads(response.data.decode("utf-8"))

    row = data["data"][1]
    assert row[3] == "alpha"
    assert row[4] == ""
    assert row[5] == ""
    assert row[6] == "100"


def test_processor_endpoint_appends_default_values(test_app_client, logged_in_rdu_user):

    # Note: default values for the test_app are ['*','*','Unclassified',960]
    # given a simple data set
    data = [["Ethnicity", "Ethnicity_type", "Value"], ["strange", "", "12"]]

    # when we call the
    response = test_app_client.post(
        url_for("cms.process_input_data"),
        data=json.dumps({"data": data}),
        content_type="application/json",
        follow_redirects=True,
    )
    data = json.loads(response.data.decode("utf-8"))

    row = data["data"][1]
    assert row[3] == "strange"
    assert row[4] == "strange"
    assert row[5] == "Unclassified"
    assert row[6] == 960

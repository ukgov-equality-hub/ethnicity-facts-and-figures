from application.cms.classification_service import ClassificationWithIncludesParentsAllUnknown
from application.data.standardisers.ethnicity_classification_finder_builder import (
    ethnicity_standardiser_from_data,
    ethnicity_classification_from_data,
    ethnicity_classification_collection_from_classification_list,
)
from application.data.ethnicity_classification_matcher import EthnicityClassificationMatcher

"""
EthnicityClassificationMatcher utilises several of the most complicated systems in rd-cms
These first methods build a testable EthnicityClassificationMatcher and all dependencies

Note from EthnicityClassificationMatcher file:
There are problems in naming when we are linking classifications to classifications
Internal refers to the database classifications. External refers to those coming from finder system
"""


def get_external_classification_simple():
    id = "2A"
    name = "White and Other"
    classification_rows = [["White", "White", "White", 1, True], ["Other", "Other", "Other", 1, True]]
    return ethnicity_classification_from_data(id=id, name=name, data_rows=classification_rows)


def get_complex_external_classification_with_parents_and_optionals():
    id = "5A+"
    name = "Has BAME as parents"
    classification_rows = [
        ["All", "All", "All", 1, False],
        ["Unknown", "Unknown", "Unknown", 1, False],
        ["BAME", "BAME", "BAME", 2, False],
        ["Asian", "Asian", "BAME", 2, True],
        ["Black", "Black", "BAME", 2, True],
        ["Mixed", "Mixed", "BAME", 2, True],
        ["Other", "Other", "BAME", 2, True],
        ["White", "White", "White", 3, True],
    ]
    return ethnicity_classification_from_data(id=id, name=name, data_rows=classification_rows)


def get_complex_external_classification_without_parents():
    id = "5A"
    name = "Does not have BAME as a parent"
    classification_rows = [
        ["All", "All", "All", 1, False],
        ["Unknown", "Unknown", "Unknown", 1, False],
        ["BAME", "BAME", "BAME", 2, False],
        ["Asian", "Asian", "Asian", 2, True],
        ["Black", "Black", "Black", 2, True],
        ["Mixed", "Mixed", "Mixed", 2, True],
        ["Other", "Other", "Other", 2, True],
        ["White", "White", "White", 3, True],
    ]
    return ethnicity_classification_from_data(id=id, name=name, data_rows=classification_rows)


def build_external_classification_collection():

    return ethnicity_classification_collection_from_classification_list(
        [
            get_external_classification_simple(),
            get_complex_external_classification_with_parents_and_optionals(),
            get_complex_external_classification_without_parents(),
        ]
    )


def build_external_standardiser():
    return ethnicity_standardiser_from_data(
        [
            ["All", "All"],
            ["Any Ethnicity", "All"],
            ["Unknown", "Unknown"],
            ["Not known", "Unknown"],
            ["Asian", "Asian"],
            ["Black", "Black"],
            ["Mixed", "Mixed"],
            ["White", "White"],
            ["Other", "Other"],
            ["BAME", "BAME"],
            ["Any ethnic minority", "BAME"],
        ]
    )


def get_test_builder():
    return EthnicityClassificationMatcher(
        ethnicity_standardiser=build_external_standardiser(),
        ethnicity_classification_collection=build_external_classification_collection(),
    )


def test_build_classification_link_returns_a_classification_link(two_classifications_2A_5A):
    # given a builder
    builder = get_test_builder()

    # when we build
    link = builder.get_classification_from_builder_values("2A", [])

    # then we have a classification link
    assert isinstance(link, ClassificationWithIncludesParentsAllUnknown)


def test_build_classification_has_all_includes_flags_as_false_by_default(two_classifications_2A_5A):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder
    input_id = "5A"
    input_values = ["Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it has correct classification id and all flags are false
    assert database_link.classification_id == "5A"
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_all_if_all_is_an_input_value(two_classifications_2A_5A):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder plus All
    input_id = "5A"
    input_values = ["All", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is True
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_all_if_synonym_for_all_is_an_input_value(two_classifications_2A_5A):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder with a value that maps to All
    input_id = "5A"
    input_values = ["Any Ethnicity", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is True
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_unknown_if_synonym_for_unknown_is_an_input_value(two_classifications_2A_5A):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder with a value that maps to All
    input_id = "5A"
    input_values = ["Not known", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is True


def test_build_classification_has_parents_if_the_classification_implements_parent_child_and_parents_are_input_values(
    two_classifications_2A_5A,
):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the values from a finder which when the id
    input_id = "5A+"
    input_values = ["BAME", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is True
    assert database_link.includes_unknown is False


def test_build_classification_does_not_have_parents_if_the_classification_does_not_implement_parent_child(
    two_classifications_2A_5A,
):
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the values from a finder which when the id
    input_id = "5A"
    input_values = ["BAME", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.get_classification_from_builder_values(input_id, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False

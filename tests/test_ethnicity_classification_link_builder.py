from application.cms.classification_service import ClassificationService
from application.cms.dimension_classification_service import ClassificationLink
from application.data.standardisers.ethnicity_classification_finder import EthnicityClassificationCollection
from application.data.standardisers.ethnicity_classification_finder_builder import (
    ethnicity_standardiser_from_data,
    ethnicity_classification_from_data,
    ethnicity_classification_collection_from_classification_list,
)
from application.data.standardisers.ethnicity_classification_link_builder import EthnicityClassificationLinkBuilder

"""
EthnicityClassificationLinkBuilder utilises several of the most complicated systems in rd-cms
These first methods build a testable EthnicityClassificationLinkBuilder and all dependencies

Note from EthnicityClassificationLinkBuilder file:
There are problems in naming when we are linking classifications to classifications
Internal refers to the database classifications. External refers to those coming from finder system
"""

internal_classification_service = ClassificationService()


def build_internal_ethnicity_classifications():
    internal_classification_service.create_classification_with_values(
        "2A", "Ethnicity", "", "White and other", values=["White", "Other"]
    )
    internal_classification_service.create_classification_with_values(
        "5A",
        "Ethnicity",
        "",
        "ONS 2011 5+1",
        values=["Asian", "Black", "Mixed", "White", "Other"],
        values_as_parent=["BAME", "White"],
    )


def get_external_classification_simple():
    code = "2A"
    name = "White and Other"
    classification_rows = [["White", "White", "White", 1, True], ["Other", "Other", "Other", 1, True]]
    return ethnicity_classification_from_data(code=code, name=name, data_rows=classification_rows)


def get_complex_external_classification_with_parents_and_optionals():
    code = "5A+"
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
    return ethnicity_classification_from_data(code=code, name=name, data_rows=classification_rows)


def get_complex_external_classification_without_parents():
    code = "5A"
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
    return ethnicity_classification_from_data(code=code, name=name, data_rows=classification_rows)


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
    build_internal_ethnicity_classifications()
    return EthnicityClassificationLinkBuilder(
        ethnicity_standardiser=build_external_standardiser(),
        ethnicity_classification_collection=build_external_classification_collection(),
        classification_service=internal_classification_service,
    )


def test_build_classification_link_returns_a_classification_link():
    # given a builder
    builder = get_test_builder()

    # when we build
    link = builder.build_internal_classification_link("2A", [])

    # then we have a classification link
    assert isinstance(link, ClassificationLink)


def test_build_classification_finds_correct_database_classification_for_finder_classification():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using simple data from a finder
    input_code = "2A"
    input_values = []
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    #
    assert database_link.get_classification().code == "2A"


def test_build_classification_has_all_includes_flags_as_false_by_default():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder
    input_code = "5A"
    input_values = ["Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.get_classification().code == "5A"
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_all_if_all_is_an_input_value():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder plus All
    input_code = "5A"
    input_values = ["All", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is True
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_all_if_synonym_for_all_is_an_input_value():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder with a value that maps to All
    input_code = "5A"
    input_values = ["Any Ethnicity", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is True
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False


def test_build_classification_has_unknown_if_synonym_for_unknown_is_an_input_value():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the basic values from a finder with a value that maps to All
    input_code = "5A"
    input_values = ["Not known", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is True


def test_build_classification_has_parents_if_the_classification_implements_parent_child_and_parents_are_input_values():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the values from a finder which when the code
    input_code = "5A+"
    input_values = ["BAME", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is True
    assert database_link.includes_unknown is False


def test_build_classification_does_not_have_parents_if_the_classification_does_not_implement_parent_child():
    # GIVEN
    # a builder
    builder = get_test_builder()

    # WHEN
    # we build a link using the values from a finder which when the code
    input_code = "5A"
    input_values = ["BAME", "Asian", "Black", "Mixed", "White", "Other"]
    database_link = builder.build_internal_classification_link(input_code, input_values)

    # THEN
    # it links to the correct classification but all flags are false
    assert database_link.includes_all is False
    assert database_link.includes_parents is False
    assert database_link.includes_unknown is False

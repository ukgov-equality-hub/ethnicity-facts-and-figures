from application.cms.classification_service import ClassificationService
from application.data.ethnicity_classification_synchroniser import EthnicityClassificationSynchroniser
from application.data.standardisers.ethnicity_classification_finder_builder import (
    ethnicity_classification_from_data,
    ethnicity_classification_collection_from_classification_list,
)

"""
A synchroniser uses the standardiser settings csv as our single source of truth

Matching is done on classification id
"""

internal_classification_service = ClassificationService()


def get_2A():
    id = "2A"
    name = "White and Other"
    classification_rows = [["White", "White", "White", 1, True], ["Other", "Other", "Other", 1, True]]
    return ethnicity_classification_from_data(id=id, name=name, data_rows=classification_rows)


def get_2A_named_test_example():
    id = "2A"
    name = "test example"
    classification_rows = [["White", "White", "White", 1, True], ["Other", "Other", "Other", 1, True]]
    return ethnicity_classification_from_data(id=id, name=name, data_rows=classification_rows)


def get_5A():
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


def get_5A_plus():
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


def reset_test_synchroniser():
    for classification in internal_classification_service.get_all_classifications():
        internal_classification_service.delete_classification(classification)

    return EthnicityClassificationSynchroniser(classification_service=internal_classification_service)


def test_synchronise_adds_external_classifications_to_internal_classification_service():
    # given a synchroniser
    synchroniser = reset_test_synchroniser()

    # when we synchronise with a very simple categorisation list
    classification_collection = ethnicity_classification_collection_from_classification_list([get_2A()])
    synchroniser.synchronise_classifications(classification_collection)

    # a classification is saved to the
    assert len(internal_classification_service.get_all_classifications()) == 1


def test_synchronise_saves_only_one_internal_classification_for_external_pair_with_and_without_parents():
    # given a synchroniser
    synchroniser = reset_test_synchroniser()

    # when we synchronise with 5A and 5A+ (which are a pair with and without parent values)
    classification_collection = ethnicity_classification_collection_from_classification_list([get_5A(), get_5A_plus()])
    synchroniser.synchronise_classifications(classification_collection)

    # then we have a classification link
    assert len(internal_classification_service.get_all_classifications()) == 1


def test_synchronise_saves_overwrites_internal_classification_name():
    # given a synchroniser
    synchroniser = reset_test_synchroniser()

    # when we synchronise values with a simple classification collection from external classification 2A
    classification_collection = ethnicity_classification_collection_from_classification_list([get_2A()])
    synchroniser.synchronise_classifications(classification_collection)

    # then we have an internal classification from 2A with expected name
    classification_2a = internal_classification_service.get_classification_by_id("2A")
    assert classification_2a.title == "White and Other"

    # when we now synchronise values with a version of 2A with an alternate name
    alt_collection = ethnicity_classification_collection_from_classification_list([get_2A_named_test_example()])
    synchroniser.synchronise_classifications(alt_collection)

    # then the internal classification now has the new expected name
    classification_2a = internal_classification_service.get_classification_by_id("2A")
    assert classification_2a.title == "test example"

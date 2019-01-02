import pytest

from application.cms.classification_service import ClassificationService
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Classification, Ethnicity

classification_service = ClassificationService()


def build_a_number_of_ethnicity_clasifications(number):
    for num in range(number):
        # Add one to make 1-based classifications
        classification_service.create_classification(f"C{num+1}", "Subfamily", f"Classification {num+1}")


def test_get_classification_by_id_does_return_classification(db_session):
    # given the london boroughs classifications
    build_a_number_of_ethnicity_clasifications(2)

    # when we get classifications by code using the classification service
    expect_c1 = classification_service.get_classification_by_id("C1")
    expect_c2 = classification_service.get_classification_by_id("C2")

    # then we expect to get the correct classifications returned
    assert expect_c1.title == "Classification 1"
    assert expect_c2.title == "Classification 2"


def test_create_classification(db_session):
    assert not Classification.query.all()

    classification = classification_service.create_classification("2B", "", "White and Other")

    assert classification == Classification.query.all()[0]


def test_delete_classification_removes_classification(db_session):
    # Given some classifications
    assert not Classification.query.all()
    build_a_number_of_ethnicity_clasifications(4)
    assert Classification.query.count() == 4

    # When we delete a classification
    classification = classification_service.get_classification_by_id("C3")
    assert classification is not None
    classification_service.delete_classification(classification=classification)

    # Then it should be deleted
    with pytest.raises(ClassificationNotFoundException):
        classification_service.get_classification_by_id("C3")
    assert Classification.query.count() == 3


def test_create_or_get_value_creates_a_value(db_session):
    assert not Ethnicity.query.all()

    value = classification_service.get_or_create_value("Purple")

    assert value is not None
    assert value.value == "Purple"


def test_create_or_get_value_recalls_existing_value(db_session):
    # given a setup with one Ethnicity value
    assert not Ethnicity.query.all()
    value = classification_service.get_or_create_value("Green")

    # when we recall the same value
    value_recalled = classification_service.get_or_create_value("Green")

    # then the original Ethnicity row is recalled
    assert value.id == value_recalled.id
    assert Ethnicity.query.count() == 1


def test_add_values_to_classification_appends_new_values(db_session):
    # given a setup with two empty classifications
    build_a_number_of_ethnicity_clasifications(2)

    classification_1 = classification_service.get_classification_by_id("C1")
    classification_2 = classification_service.get_classification_by_id("C2")
    assert len(classification_1.ethnicities) == 0
    assert len(classification_2.ethnicities) == 0

    # when we add some values to the empty classifications
    classification_service.add_values_to_classification(classification_1, ["Green", "Red", "Purple"])
    classification_service.add_values_to_classification(classification_2, ["Red", "Pink"])

    # then the values have been added
    assert len(classification_1.ethnicities) == 3
    assert len(classification_2.ethnicities) == 2

    # And all classifications containing a particular value can be found
    red = classification_service.get_or_create_value("Red")
    pink = classification_service.get_or_create_value("Pink")
    assert len(red.classifications) == 2
    assert len(pink.classifications) == 1
    assert set(red.classifications) == set([classification_1, classification_2])
    assert pink.classifications == [classification_2]


def test_remove_value_from_classification_removes_value(db_session):
    # given a setup with two classifications with values
    build_a_number_of_ethnicity_clasifications(2)
    classification_1 = classification_service.get_classification_by_id("C1")
    classification_2 = classification_service.get_classification_by_id("C2")
    classification_service.add_values_to_classification(classification_1, ["Green", "Red", "Purple"])
    classification_service.add_values_to_classification(classification_2, ["Red", "Pink"])

    # when we remove a value from one classification that also exisits in the second classification
    classification_service.remove_value_from_classification(classification_2, "Red")

    # then the value is gone from the specified classification but still exists in the other classification
    red = classification_service.get_value("Red")
    assert len(red.classifications) == 1
    assert len(classification_1.ethnicities) == 3
    assert len(classification_2.ethnicities) == 1
    assert "Classification 2" not in [c.title for c in red.classifications]
    assert "Red" not in [c.value for c in classification_2.ethnicities]
    assert "Red" in [c.value for c in classification_1.ethnicities]


def test_add_parent_value_to_classification_appends_new_parent(db_session):
    # given a setup with one classification
    people = ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]

    # Create classifications (also commits them to the database).
    classification_service.create_classification_with_values("G1", "Teams", "Race Disparity Unit", values=people)

    rdu_by_tribe = classification_service.create_classification_with_values(
        "G2", "Teams", "Race Disparity Unit by Tribe", values=people
    )
    rdu_by_gender = classification_service.create_classification_with_values(
        "G3", "Teams", "Race Disparity Unit by Gender", values=people
    )

    # when we link to parents
    classification_service.add_values_to_classification_as_parents(rdu_by_gender, ["Male", "Female"])
    classification_service.add_values_to_classification_as_parents(rdu_by_tribe, ["Data", "Digital", "Policy"])

    # then
    standard = classification_service.get_classification_by_id("G1")
    by_tribe = classification_service.get_classification_by_id("G2")
    by_gender = classification_service.get_classification_by_id("G3")
    assert len(standard.parent_values) == 0
    assert len(by_tribe.parent_values) == 3
    assert len(by_gender.parent_values) == 2


def test_remove_parent_value_from_classification_removes_value(db_session):
    # given a setup with one classification
    people = ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]
    classification_service.create_classification_with_values(
        "G2", "Teams", "Race Disparity Unit by Tribe", values=people
    )
    by_tribe = classification_service.get_classification_by_id("G2")
    classification_service.add_values_to_classification_as_parents(by_tribe, ["Data", "Digital", "Policy"])

    # when
    classification_service.remove_parent_value_from_classification(by_tribe, "Digital")

    # then
    by_tribe = classification_service.get_classification_by_id("G2")
    assert len(by_tribe.parent_values) == 2

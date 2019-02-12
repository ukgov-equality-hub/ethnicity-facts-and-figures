import pytest

from application.cms.classification_service import ClassificationService
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Classification, Ethnicity

from tests.models import ClassificationFactory, EthnicityFactory

classification_service = ClassificationService()


def test_get_classification_by_id_does_return_classification():
    c1, c2 = ClassificationFactory(id="C1"), ClassificationFactory(id="C2")

    # when we get classifications by code using the classification service
    expect_c1 = classification_service.get_classification_by_id("C1")
    expect_c2 = classification_service.get_classification_by_id("C2")

    # then we expect to get the correct classifications returned
    assert expect_c1 is c1
    assert expect_c2 is c2


def test_create_classification():
    classification = classification_service.create_classification("2B", "", "White and Other")

    assert classification == Classification.query.get("2B")


def test_delete_classification_removes_classification():
    # Given some classifications
    ClassificationFactory(id="C1")
    ClassificationFactory(id="C2")
    ClassificationFactory(id="C3")
    ClassificationFactory(id="C4")
    assert Classification.query.count() == 4

    # When we delete a classification
    classification = classification_service.get_classification_by_id("C3")
    assert classification is not None
    classification_service.delete_classification(classification=classification)

    # Then it should be deleted
    with pytest.raises(ClassificationNotFoundException):
        classification_service.get_classification_by_id("C3")
    assert Classification.query.count() == 3


def test_create_or_get_value_creates_a_value():
    assert not Ethnicity.query.all()

    value = classification_service.get_or_create_value("Purple")

    assert value is not None
    assert value.value == "Purple"


def test_create_or_get_value_recalls_existing_value():
    # given a setup with one Ethnicity value
    assert not Ethnicity.query.all()
    value = classification_service.get_or_create_value("Green")

    # when we recall the same value
    value_recalled = classification_service.get_or_create_value("Green")

    # then the original Ethnicity row is recalled
    assert value.id == value_recalled.id
    assert Ethnicity.query.count() == 1


def test_add_values_to_classification_appends_new_values():
    # given a setup with two empty classifications
    c1, c2 = (
        ClassificationFactory(id="C1", ethnicities=[], parent_values=[]),
        ClassificationFactory(id="C2", ethnicities=[], parent_values=[]),
    )

    assert len(c1.ethnicities) == 0
    assert len(c2.ethnicities) == 0

    # when we add some values to the empty classifications
    classification_service.add_values_to_classification(c1, ["Green", "Red", "Purple"])
    classification_service.add_values_to_classification(c2, ["Red", "Pink"])

    # then the values have been added
    assert len(c1.ethnicities) == 3
    assert len(c2.ethnicities) == 2

    # And all classifications containing a particular value can be found
    red = classification_service.get_or_create_value("Red")
    pink = classification_service.get_or_create_value("Pink")
    assert len(red.classifications) == 2
    assert len(pink.classifications) == 1
    assert set(red.classifications) == set([c1, c2])
    assert pink.classifications == [c2]


def test_remove_value_from_classification_removes_value():
    # given a setup with two classifications with values
    ethnicities = {colour.lower(): EthnicityFactory(value=colour) for colour in ["Green", "Red", "Purple", "Pink"]}
    c1, c2 = (
        ClassificationFactory(
            id="C1",
            title="Classification 1",
            ethnicities=[ethnicities["green"], ethnicities["red"], ethnicities["purple"]],
            parent_values=[],
        ),
        ClassificationFactory(
            id="C2", title="Classification 2", ethnicities=[ethnicities["red"], ethnicities["pink"]], parent_values=[]
        ),
    )

    # when we remove a value from one classification that also exisits in the second classification
    classification_service.remove_value_from_classification(c2, "Red")

    # then the value is gone from the specified classification but still exists in the other classification
    red = classification_service.get_value("Red")
    assert len(red.classifications) == 1
    assert len(c1.ethnicities) == 3
    assert len(c2.ethnicities) == 1
    assert "Classification 2" not in [c.title for c in red.classifications]
    assert "Red" not in [c.value for c in c2.ethnicities]
    assert "Red" in [c.value for c in c1.ethnicities]


def test_add_parent_value_to_classification_appends_new_parent():
    # given a setup with one classification
    people = [
        EthnicityFactory(value=person)
        for person in ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]
    ]

    # Create classifications (also commits them to the database).
    g1 = ClassificationFactory(
        id="G1", title="Teams", long_title="Race Disparity Unit", ethnicities=people, parent_values=[]
    )
    g2 = ClassificationFactory(
        id="G2", title="Teams", long_title="Race Disparity Unit by Tribe", ethnicities=people, parent_values=[]
    )
    g3 = ClassificationFactory(
        id="G3", title="Teams", long_title="Race Disparity Unit by Gender", ethnicities=people, parent_values=[]
    )

    # when we link to parents
    classification_service.add_values_to_classification_as_parents(g2, ["Data", "Digital", "Policy"])
    classification_service.add_values_to_classification_as_parents(g3, ["Male", "Female"])

    # then
    assert len(g1.parent_values) == 0
    assert len(g2.parent_values) == 3
    assert len(g3.parent_values) == 2


def test_remove_parent_value_from_classification_removes_value():
    # given a setup with one classification
    people = [
        EthnicityFactory(value=person)
        for person in ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]
    ]
    g2 = ClassificationFactory(
        id="G2", title="Teams", long_title="Race Disparity Unit by Tribe", ethnicities=people, parent_values=[]
    )

    # when we add some parent values
    classification_service.add_values_to_classification_as_parents(g2, ["Data", "Digital", "Policy"])

    # then we have all of those parent values for the classification
    assert len(g2.parent_values) == 3

    # when we remove one of the parent values
    classification_service.remove_parent_value_from_classification(g2, "Digital")

    # then we have one fewer parent values for the classification
    assert len(g2.parent_values) == 2

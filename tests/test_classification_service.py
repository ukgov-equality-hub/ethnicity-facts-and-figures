import pytest

from application.cms.classification_service import ClassificationService
from application.cms.dimension_classification_service import ClassificationLink
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Classification, ClassificationValue

classification_service = ClassificationService()


def build_london_boroughs():
    classification_service.create_classification_with_values(
        "L1", "Geography", "Local level", "Greater London Boroughs", values=["Barnet", "Camden", "Ealing", "Haringey"]
    )
    classification_service.create_classification_with_values(
        "L2", "Geography", "Local level", "Inner London Boroughs", values=["Camden", "Haringey"]
    )


def build_colours():
    classification_service.create_classification_with_values("C1", "Colours", "Paint", "Cars", values=["Red", "Black"])
    classification_service.create_classification_with_values("C2", "Colours", "Paint", "Nails", values=["Pink", "Red"])


def test_get_classification_by_code_does_return_classification(db_session):
    # given the london boroughs classifications
    build_london_boroughs()

    # when we get classifications by code using the classification service
    expect_greater_london = classification_service.get_classification_by_code("Geography", "L1")
    expect_inner_london = classification_service.get_classification_by_code("Geography", "L2")

    # then we expect to get the correct classifications returned
    assert expect_greater_london.title == "Greater London Boroughs"
    assert expect_inner_london.title == "Inner London Boroughs"


def test_add_classification_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given a dimension and the "greater london" classification
    build_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]
    greater_london = classification_service.get_classification_by_code("Geography", "L1")

    # when we link the dimension to the classification
    classification_link = ClassificationLink(greater_london.id)
    classification_service.link_classification_to_dimension(dimension, classification_link)

    # then
    dimension = stub_page_with_dimension.dimensions[0]
    assert dimension.classification_links.count() == 1
    assert greater_london.dimension_links.count() == 1


def test_link_classification_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given
    build_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    # when
    link_dimension_to_greater_london_boroughs(dimension)

    # then
    # the dimension links and classification links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_code("Geography", "L1")
    assert dimension.classification_links.count() == 1
    assert classification.dimension_links.count() == 1


def test_link_classification_to_dimension_does_save_data_properties(db_session, stub_page_with_dimension):
    # given a classification that contains boroughs in greater london
    build_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    # when we associate a dimension
    link_dimension_to_greater_london_boroughs(dimension)

    # then
    # the dimension is associated with the classification
    dimension = stub_page_with_dimension.dimensions[0]
    assert "Greater London Boroughs" == dimension.classification_links[0].classification.title


def test_get_classification_from_dimension_by_family_does_get_correct_classification(
    db_session, stub_page_with_dimension
):
    # given a dimension that is linked to two families of classification
    build_london_boroughs()
    build_colours()
    dimension = stub_page_with_dimension.dimensions[0]

    link_dimension_to_greater_london_boroughs(dimension)
    link_dimension_to_colours(dimension)

    # when we request classifications by family for this dimension
    greater_london_expected = classification_service.get_classification_link_for_dimension_by_family(
        dimension, "Geography"
    )
    cars_expected = classification_service.get_classification_link_for_dimension_by_family(dimension, "Colours")
    none_expected = classification_service.get_classification_link_for_dimension_by_family(dimension, "Professions")

    # then
    # the classifications should be correct for each family or None if the family is not found
    assert greater_london_expected.classification.title == "Greater London Boroughs"
    assert cars_expected.classification.title == "Cars"
    assert none_expected is None


def link_dimension_to_greater_london_boroughs(dimension, parents=False, all=False, unknown=False):
    greater_london = classification_service.get_classification_by_code("Geography", "L1")
    link = ClassificationLink(greater_london.id, parents, all, unknown)
    classification_service.link_classification_to_dimension(dimension, link)


def link_dimension_to_colours(dimension, parents=False, all=False, unknown=False):
    colours = classification_service.get_classification_by_code("Colours", "C1")
    link = ClassificationLink(colours.id, parents, all, unknown)
    classification_service.link_classification_to_dimension(dimension, link)


def test_link_classification_to_dimension_does_remove_link(db_session, stub_page_with_dimension):
    # given a dimension linked to the greater london boroughs
    build_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]
    link_dimension_to_greater_london_boroughs(dimension)

    # when we remove that link
    greater_london = classification_service.get_classification_by_title("Geography", "Greater London Boroughs")
    classification_service.unlink_classification_from_dimension(
        dimension=stub_page_with_dimension.dimensions[0], classification=greater_london
    )

    # then
    # the association is removed from the dimension and the classification
    dimension = stub_page_with_dimension.dimensions[0]
    greater_london = classification_service.get_classification_by_title("Geography", "Greater London Boroughs")
    assert dimension.classification_links.count() == 0
    assert greater_london.dimension_links.count() == 0


def test_create_classification(db_session):
    assert not Classification.query.all()

    classification = classification_service.create_classification("Geography", "Region")

    assert classification == Classification.query.all()[0]


def test_get_classification_returns_classification(db_session):
    assert not Classification.query.all()

    classification_service.create_classification("G1", "Geography", "Regional Geography", "Region 1")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")
    classification_service.create_classification("G3", "Geography", "Regional Geography", "Region 3")
    classification_service.create_classification("G4", "Geography", "Regional Geography", "Region 4")
    classification_service.create_classification("U1", "UK Geography", "UK Regional Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")

    assert classification is not None
    assert classification.title == "Region 2"
    assert classification.family == "Geography"


def test_get_classification_returns_none_for_not_found(db_session):
    assert not Classification.query.all()

    classification_service.create_classification("Geography", "Region 1")
    classification_service.create_classification("Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")
    missing_classification = classification_service.get_classification_by_title("Fish", "Chips")

    assert classification is not None
    assert missing_classification is None


def test_delete_classification_removes_classification(db_session):
    # Given some classifications
    assert not Classification.query.all()
    classification_service.create_classification("G1", "Geography", "Regional Geography", "Region 1")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")
    classification_service.create_classification("G3", "Geography", "Regional Geography", "Region 3")
    classification_service.create_classification("G4", "Geography", "Regional Geography", "Region 4")

    # When we delete a classification
    classification = classification_service.get_classification_by_title("Geography", "Region 3")
    assert classification is not None
    classification_service.delete_classification(classification=classification)

    # Then it should be deleted
    with pytest.raises(ClassificationNotFoundException):
        classification_service.get_classification_by_title("Geography", "Region 3")
    assert Classification.query.count() == 3


def test_create_classification(db_session):
    assert not Classification.query.all()

    classification = classification_service.create_classification("G1", "Geography", "National level", "Region")

    assert classification == Classification.query.all()[0]


def test_get_classification_returns_classification(db_session):
    assert not Classification.query.all()

    classification_service.create_classification("G1", "Geography", "Regional Geography", "Region 1")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")
    classification_service.create_classification("G3", "Geography", "Regional Geography", "Region 3")
    classification_service.create_classification("G4", "Geography", "Regional Geography", "Region 4")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")

    assert classification is not None
    assert classification.title == "Region 2"
    assert classification.family == "Geography"


def test_get_classification_returns_none_for_not_found(db_session):
    assert not Classification.query.all()

    classification_service.create_classification("G1", "Geography", "Regional Geography", "Region 1")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")
    assert classification is not None

    with pytest.raises(ClassificationNotFoundException):
        classification_service.get_classification_by_title("Fish", "Chips")


def test_create_value_creates_a_value(db_session):
    assert not ClassificationValue.query.all()

    value = classification_service.create_or_get_value("Camden")

    assert value is not None
    assert value.value == "Camden"


def test_create_or_get_value_recalls_existing_value(db_session):
    # given a setup with one
    assert not ClassificationValue.query.all()
    value = classification_service.create_or_get_value("Camden")

    # when we recall the value
    value_recalled = classification_service.create_or_get_value("Camden")

    # then the
    assert value.id == value_recalled.id
    assert ClassificationValue.query.count() == 1


def test_add_value_to_classification_appends_new_value(db_session):
    # given a setup with one
    classification_service.create_classification("G1", "Geography", "Local level", "Greater London Boroughs")
    classification_service.create_classification("G2", "Geography", "Local level", "Inner London Boroughs")

    greater_london = classification_service.get_classification_by_code("Geography", "G1")
    inner_london = classification_service.get_classification_by_code("Geography", "G2")

    classification_service.add_values_to_classification(greater_london, ["Barnet", "Camden", "Haringey"])
    classification_service.add_values_to_classification(inner_london, ["Camden", "Haringey"])

    # then the
    greater_london = classification_service.get_classification_by_title("Geography", "Greater London Boroughs")
    inner_london = classification_service.get_classification_by_title("Geography", "Inner London Boroughs")
    camden = classification_service.create_or_get_value("Camden")

    assert len(camden.classifications) == 2
    assert len(greater_london.values) == 3
    assert len(inner_london.values) == 2


def test_remove_value_from_classification_removes_value(db_session):
    # given a setup with one
    greater_london = classification_service.create_classification(
        "G1", "Geography", "Local level", "Greater London Boroughs"
    )
    inner_london = classification_service.create_classification(
        "G2", "Geography", "Local level", "Inner London Boroughs"
    )

    classification_service.add_values_to_classification(greater_london, ["Barnet", "Camden", "Haringey"])
    classification_service.add_values_to_classification(inner_london, ["Camden", "Haringey"])

    # when we remove the value
    classification_service.remove_value_from_classification(inner_london, "Camden")

    # then the
    camden = classification_service.get_value("Camden")

    assert len(camden.classifications) == 1
    assert len(greater_london.values) == 3
    assert len(inner_london.values) == 1
    assert "Inner London Boroughs" not in [c.title for c in camden.classifications]
    assert "Camden" not in [c.value for c in inner_london.values]
    assert "Camden" in [c.value for c in greater_london.values]


def test_add_parent_value_to_classification_appends_new_parent(db_session):
    # given a setup with one classification
    people = ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]
    rdu = classification_service.create_classification_with_values(
        "G1", "People", "Teams", "Race Disparity Unit", values=people
    )
    rdu_by_tribe = classification_service.create_classification_with_values(
        "G2", "People", "Teams", "Race Disparity Unit by Tribe", values=people
    )
    rdu_by_gender = classification_service.create_classification_with_values(
        "G3", "People", "Teams", "Race Disparity Unit by Gender", values=people
    )

    # when we link to parents
    classification_service.add_values_to_classification_as_parents(rdu_by_gender, ["Male", "Female"])
    classification_service.add_values_to_classification_as_parents(rdu_by_tribe, ["Data", "Digital", "Policy"])

    # then
    standard = classification_service.get_classification_by_title("People", "Race Disparity Unit")
    by_tribe = classification_service.get_classification_by_title("People", "Race Disparity Unit by Tribe")
    by_gender = classification_service.get_classification_by_title("People", "Race Disparity Unit by Gender")
    assert len(standard.parent_values) == 0
    assert len(by_tribe.parent_values) == 3
    assert len(by_gender.parent_values) == 2


def test_remove_parent_value_from_classification_removes_value(db_session):
    # given a setup with one classification
    people = ["Tom", "Frankie", "Caroline", "Adam", "Cath", "Marcus", "Sylvia", "Katerina"]
    classification_service.create_classification_with_values(
        "G2", "People", "Teams", "Race Disparity Unit by Tribe", values=people
    )
    by_tribe = classification_service.get_classification_by_title("People", "Race Disparity Unit by Tribe")
    classification_service.add_values_to_classification_as_parents(by_tribe, ["Data", "Digital", "Policy"])

    # when
    classification_service.remove_parent_value_from_classification(by_tribe, "Digital")

    # then
    by_tribe = classification_service.get_classification_by_title("People", "Race Disparity Unit by Tribe")
    assert len(by_tribe.parent_values) == 2

import pytest

from application.cms.classification_service import ClassificationService
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Categorisation, CategorisationValue

classification_service = ClassificationService()


def build_greater_london_boroughs():
    classification_service.create_classification_with_values(
        "L1", "Geography", "Local level", "Greater London Boroughs", values=["Barnet", "Camden", "Ealing", "Haringey"]
    )
    classification_service.create_classification_with_values(
        "L2", "Geography", "Local level", "Inner London Boroughs", values=["Camden", "Haringey"]
    )


def build_colours():
    classification_service.create_classification_with_values("C1", "Colours", "Paint", "Cars", values=["Red", "Black"])
    classification_service.create_classification_with_values("C2", "Colours", "Paint", "Nails", values=["Pink", "Red"])


def test_get_classification_by_id_does_return_classification(db_session):
    # given
    build_greater_london_boroughs()

    # when
    expect_greater_london = classification_service.get_classification_by_code("L1")
    expect_inner_london = classification_service.get_classification_by_code("L2")

    # then
    assert expect_greater_london.title == "Greater London Boroughs"
    assert expect_inner_london.title == "Inner London Boroughs"


def test_add_classification_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    # when
    classification = classification_service.get_classification_by_code("L1")
    classification_service.link_classification_to_dimension(
        dimension, classification, includes_parents=False, includes_all=False, includes_unknown=False
    )

    # then
    # check links all add up
    dimension = stub_page_with_dimension.dimensions[0]
    assert dimension.categorisation_links.count() == 1
    assert classification.dimension_links.count() == 1


def test_link_classification_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()

    dimension = stub_page_with_dimension.dimensions[0]

    # when
    classification = classification_service.get_classification_by_code("L1")
    classification_service.link_classification_to_dimension(
        dimension, classification, includes_parents=False, includes_all=True, includes_unknown=False
    )

    # then
    # the dimension links and classification links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_code("L1")
    assert dimension.categorisation_links.count() == 1
    assert classification.dimension_links.count() == 1


def test_link_classification_to_dimension_does_save_data_properties(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()

    dimension = stub_page_with_dimension.dimensions[0]

    # when
    classification = classification_service.get_classification_by_code("L1")
    classification_service.link_classification_to_dimension(
        dimension, classification=classification, includes_parents=False, includes_all=True, includes_unknown=False
    )

    # then
    # the dimension links and classification links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    categorisation_link = dimension.categorisation_links[0]
    assert categorisation_link.includes_parents is False
    assert categorisation_link.includes_all is True
    assert categorisation_link.includes_unknown is False


def test_get_classification_from_dimension_by_family_does_get_correct_classification(db_session, stub_page_with_dimension):
    # given a page linked to some categories
    build_greater_london_boroughs()
    build_colours()
    dimension = stub_page_with_dimension.dimensions[0]

    greater_london = classification_service.get_classification_by_code("L1")
    classification_service.link_classification_to_dimension(
        dimension, classification=greater_london, includes_parents=False, includes_all=True, includes_unknown=False
    )
    car_colours = classification_service.get_classification_by_code("C1")
    classification_service.link_classification_to_dimension(
        dimension, classification=car_colours, includes_parents=False, includes_all=True, includes_unknown=False
    )
    # when we request
    greater_london_expected = classification_service.get_classification_link_for_dimension_by_family(
        dimension, "Geography"
    )
    cars_expected = classification_service.get_classification_link_for_dimension_by_family(dimension, "Colours")
    none_expected = classification_service.get_classification_link_for_dimension_by_family(dimension, "Professions")

    # then
    # the categories we get back should b
    assert greater_london_expected.categorisation.title == "Greater London Boroughs"
    assert cars_expected.categorisation.title == "Cars"
    assert none_expected is None


def test_link_classification_to_dimension_does_remove_link(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    greater_london = classification_service.get_classification_by_code("L1")
    classification_service.link_classification_to_dimension(
        dimension, classification=greater_london, includes_parents=False, includes_all=True, includes_unknown=False
    )

    # when
    classification_service.unlink_classification_from_dimension(
        dimension=stub_page_with_dimension.dimensions[0], classification=greater_london
    )

    # then
    # the dimension links and classification links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_title("Geography", "Greater London Boroughs")
    assert dimension.categorisation_links.count() == 0
    assert classification.dimension_links.count() == 0


def test_create_classification(db_session):
    assert not Categorisation.query.all()

    classification = classification_service.create_classification("Geography", "Region")

    assert classification == Categorisation.query.all()[0]


def test_get_classification_returns_classification(db_session):
    assert not Categorisation.query.all()

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
    assert not Categorisation.query.all()

    classification_service.create_classification("Geography", "Region 1")
    classification_service.create_classification("Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")
    missing_categorisation = classification_service.get_classification_by_title("Fish", "Chips")

    assert classification is not None
    assert missing_categorisation is None


def test_delete_classification_removes_classification(db_session):
    # Given some categories
    assert not Categorisation.query.all()
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
    assert Categorisation.query.count() == 3


def test_create_classification(db_session):
    assert not Categorisation.query.all()

    classification = classification_service.create_classification("G1", "Geography", "National level", "Region")

    assert classification == Categorisation.query.all()[0]


def test_get_classification_returns_classification(db_session):
    assert not Categorisation.query.all()

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
    assert not Categorisation.query.all()

    classification_service.create_classification("G1", "Geography", "Regional Geography", "Region 1")
    classification_service.create_classification("G2", "Geography", "Regional Geography", "Region 2")

    classification = classification_service.get_classification_by_title("Geography", "Region 2")
    assert classification is not None

    with pytest.raises(ClassificationNotFoundException):
        classification_service.get_classification_by_title("Fish", "Chips")


def test_create_value_creates_a_value(db_session):
    assert not CategorisationValue.query.all()

    value = classification_service.create_or_get_value("Camden")

    assert value is not None
    assert value.value == "Camden"


def test_create_or_get_value_recalls_existing_value(db_session):
    # given a setup with one
    assert not CategorisationValue.query.all()
    value = classification_service.create_or_get_value("Camden")

    # when we recall the value
    value_recalled = classification_service.create_or_get_value("Camden")

    # then the
    assert value.id == value_recalled.id
    assert CategorisationValue.query.count() == 1


def test_add_value_to_classification_appends_new_value(db_session):
    # given a setup with one
    classification_service.create_classification("G1", "Geography", "Local level", "Greater London Boroughs")
    classification_service.create_classification("G2", "Geography", "Local level", "Inner London Boroughs")

    greater_london = classification_service.get_classification_by_code("G1")
    inner_london = classification_service.get_classification_by_code("G2")

    classification_service.add_values_to_classification(greater_london, ["Barnet", "Camden", "Haringey"])
    classification_service.add_values_to_classification(inner_london, ["Camden", "Haringey"])

    # then the
    greater_london = classification_service.get_classification_by_title("Geography", "Greater London Boroughs")
    inner_london = classification_service.get_classification_by_title("Geography", "Inner London Boroughs")
    camden = classification_service.create_or_get_value("Camden")

    assert len(camden.categorisations) == 2
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

    assert len(camden.categorisations) == 1
    assert len(greater_london.values) == 3
    assert len(inner_london.values) == 1
    assert "Inner London Boroughs" not in [c.title for c in camden.categorisations]
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

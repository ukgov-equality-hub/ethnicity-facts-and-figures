import pytest

from datetime import datetime, timedelta

from application.cms.categorisation_service import CategorisationService
from application.cms.exceptions import RejectionImpossible, CategorisationNotFoundException
from application.cms.models import Page, Dimension, DimensionCategorisation, Categorisation, CategorisationValue

categorisation_service = CategorisationService()


def build_greater_london_boroughs():
    categorisation_service.create_categorisation_with_values('L1', 'Geography', 'Local level',
                                                             'Greater London Boroughs',
                                                             values=['Barnet', 'Camden', 'Ealing', 'Haringey'])
    categorisation_service.create_categorisation_with_values('L2', 'Geography', 'Local level', 'Inner London Boroughs',
                                                             values=['Camden', 'Haringey'])


def build_colours():
    categorisation_service.create_categorisation_with_values('C1', 'Colours', 'Paint', 'Cars',
                                                             values=['Red', 'Black'])
    categorisation_service.create_categorisation_with_values('C2', 'Colours', 'Paint', 'Nails',
                                                             values=['Pink', 'Red'])


def test_get_category_by_id_does_return_category(db_session):
    # given
    build_greater_london_boroughs()

    # when
    expect_greater_london = categorisation_service.get_categorisation_by_code('L1')
    expect_inner_london = categorisation_service.get_categorisation_by_code('L2')

    # then
    assert expect_greater_london.title == 'Greater London Boroughs'
    assert expect_inner_london.title == 'Inner London Boroughs'


def test_add_category_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    # when
    categorisation = categorisation_service.get_categorisation_by_code('L1')
    categorisation_service.link_categorisation_to_dimension(dimension, categorisation, includes_parents=False,
                                                            includes_all=False, includes_unknown=False)

    # then
    # check links all add up
    dimension = stub_page_with_dimension.dimensions[0]
    assert dimension.categorisation_links.count() == 1
    assert categorisation.dimension_links.count() == 1


def test_link_category_to_dimension_does_append(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()

    dimension = stub_page_with_dimension.dimensions[0]

    # when
    categorisation = categorisation_service.get_categorisation_by_code('L1')
    categorisation_service.link_categorisation_to_dimension(dimension, categorisation, includes_parents=False,
                                                            includes_all=True, includes_unknown=False)

    # then
    # the dimension links and category links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    categorisation = categorisation_service.get_categorisation_by_code('L1')
    assert dimension.categorisation_links.count() == 1
    assert categorisation.dimension_links.count() == 1


def test_link_category_to_dimension_does_save_data_properties(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()

    dimension = stub_page_with_dimension.dimensions[0]

    # when
    categorisation = categorisation_service.get_categorisation_by_code('L1')
    categorisation_service.link_categorisation_to_dimension(dimension,
                                                            categorisation=categorisation,
                                                            includes_parents=False,
                                                            includes_all=True,
                                                            includes_unknown=False)

    # then
    # the dimension links and category links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    categorisation_link = dimension.categorisation_links[0]
    assert categorisation_link.includes_parents is False
    assert categorisation_link.includes_all is True
    assert categorisation_link.includes_unknown is False


def test_get_category_from_dimension_by_family_does_get_correct_category(db_session, stub_page_with_dimension):
    # given a page linked to some categories
    build_greater_london_boroughs()
    build_colours()
    dimension = stub_page_with_dimension.dimensions[0]

    greater_london = categorisation_service.get_categorisation_by_code('L1')
    categorisation_service.link_categorisation_to_dimension(dimension,
                                                            categorisation=greater_london,
                                                            includes_parents=False,
                                                            includes_all=True,
                                                            includes_unknown=False)
    car_colours = categorisation_service.get_categorisation_by_code('C1')
    categorisation_service.link_categorisation_to_dimension(dimension,
                                                            categorisation=car_colours,
                                                            includes_parents=False,
                                                            includes_all=True,
                                                            includes_unknown=False)
    # when we request
    greater_london_expected = categorisation_service.get_categorisation_link_for_dimension_by_family(dimension,
                                                                                                     'Geography')
    cars_expected = categorisation_service.get_categorisation_link_for_dimension_by_family(dimension, 'Colours')
    none_expected = categorisation_service.get_categorisation_link_for_dimension_by_family(dimension, 'Professions')

    # then
    # the categories we get back should b
    assert greater_london_expected.categorisation.title == 'Greater London Boroughs'
    assert cars_expected.categorisation.title == 'Cars'
    assert none_expected is None


def test_link_category_to_dimension_does_remove_link(db_session, stub_page_with_dimension):
    # given
    build_greater_london_boroughs()
    dimension = stub_page_with_dimension.dimensions[0]

    greater_london = categorisation_service.get_categorisation_by_code('L1')
    categorisation_service.link_categorisation_to_dimension(dimension,
                                                            categorisation=greater_london,
                                                            includes_parents=False,
                                                            includes_all=True,
                                                            includes_unknown=False)

    # when
    categorisation_service.unlink_categorisation_from_dimension(dimension=stub_page_with_dimension.dimensions[0],
                                                                categorisation=greater_london)

    # then
    # the dimension links and category links save in place
    dimension = stub_page_with_dimension.dimensions[0]
    categorisation = categorisation_service.get_categorisation('Geography', 'Greater London Boroughs')
    assert dimension.categorisation_links.count() == 0
    assert categorisation.dimension_links.count() == 0


def test_create_category(db_session):
    assert not Categorisation.query.all()

    categorisation = categorisation_service.create_categorisation('Geography', 'Region')

    assert categorisation == Categorisation.query.all()[0]


def test_get_category_returns_category(db_session):
    assert not Categorisation.query.all()

    categorisation_service.create_categorisation('G1', 'Geography', 'Regional Geography', 'Region 1')
    categorisation_service.create_categorisation('G2', 'Geography', 'Regional Geography', 'Region 2')
    categorisation_service.create_categorisation('G3', 'Geography', 'Regional Geography', 'Region 3')
    categorisation_service.create_categorisation('G4', 'Geography', 'Regional Geography', 'Region 4')
    categorisation_service.create_categorisation('U1', 'UK Geography', 'UK Regional Geography', 'Region 2')

    categorisation = categorisation_service.get_categorisation('Geography', 'Region 2')

    assert categorisation is not None
    assert categorisation.title == 'Region 2'
    assert categorisation.family == 'Geography'


def test_get_category_returns_none_for_not_found(db_session):
    assert not Categorisation.query.all()

    categorisation_service.create_categorisation('Geography', 'Region 1')
    categorisation_service.create_categorisation('Geography', 'Region 2')

    categorisation = categorisation_service.get_categorisation('Geography', 'Region 2')
    missing_categorisation = categorisation_service.get_categorisation('Fish', 'Chips')

    assert categorisation is not None
    assert missing_categorisation is None


def test_delete_category_removes_category(db_session):
    # Given some categories
    assert not Categorisation.query.all()
    categorisation_service.create_categorisation('G1', 'Geography', 'Regional Geography', 'Region 1')
    categorisation_service.create_categorisation('G2', 'Geography', 'Regional Geography', 'Region 2')
    categorisation_service.create_categorisation('G3', 'Geography', 'Regional Geography', 'Region 3')
    categorisation_service.create_categorisation('G4', 'Geography', 'Regional Geography', 'Region 4')

    # When we delete a category
    categorisation = categorisation_service.get_categorisation('Geography', 'Region 3')
    assert categorisation is not None
    categorisation_service.delete_categorisation(categorisation=categorisation)

    # Then it should be deleted
    with pytest.raises(CategorisationNotFoundException):
        categorisation_service.get_categorisation('Geography', 'Region 3')
    assert Categorisation.query.count() == 3


def test_create_category(db_session):
    assert not Categorisation.query.all()

    categorisation = categorisation_service.create_categorisation('G1', 'Geography', 'National level', 'Region')

    assert categorisation == Categorisation.query.all()[0]


def test_get_category_returns_category(db_session):
    assert not Categorisation.query.all()

    categorisation_service.create_categorisation('G1', 'Geography', 'Regional Geography', 'Region 1')
    categorisation_service.create_categorisation('G2', 'Geography', 'Regional Geography', 'Region 2')
    categorisation_service.create_categorisation('G3', 'Geography', 'Regional Geography', 'Region 3')
    categorisation_service.create_categorisation('G4', 'Geography', 'Regional Geography', 'Region 4')
    categorisation_service.create_categorisation('G2', 'Geography', 'Regional Geography', 'Region 2')

    categorisation = categorisation_service.get_categorisation('Geography', 'Region 2')

    assert categorisation is not None
    assert categorisation.title == 'Region 2'
    assert categorisation.family == 'Geography'


def test_get_category_returns_none_for_not_found(db_session):
    assert not Categorisation.query.all()

    categorisation_service.create_categorisation('G1', 'Geography', 'Regional Geography', 'Region 1')
    categorisation_service.create_categorisation('G2', 'Geography', 'Regional Geography', 'Region 2')

    categorisation = categorisation_service.get_categorisation('Geography', 'Region 2')
    assert categorisation is not None

    with pytest.raises(CategorisationNotFoundException):
        categorisation_service.get_categorisation('Fish', 'Chips')


def test_create_value_creates_a_value(db_session):
    assert not CategorisationValue.query.all()

    value = categorisation_service.create_or_get_value('Camden')

    assert value is not None
    assert value.value == 'Camden'


def test_create_or_get_value_recalls_existing_value(db_session):
    # given a setup with one
    assert not CategorisationValue.query.all()
    value = categorisation_service.create_or_get_value('Camden')

    # when we recall the value
    value_recalled = categorisation_service.create_or_get_value('Camden')

    # then the
    assert value.id == value_recalled.id
    assert CategorisationValue.query.count() == 1


def test_add_value_to_category_appends_new_value(db_session):
    # given a setup with one
    categorisation_service.create_categorisation('G1', 'Geography', 'Local level', 'Greater London Boroughs')
    categorisation_service.create_categorisation('G2', 'Geography', 'Local level', 'Inner London Boroughs')

    greater_london = categorisation_service.get_categorisation_by_code('G1')
    inner_london = categorisation_service.get_categorisation_by_code('G2')

    categorisation_service.add_values_to_categorisation(greater_london,
                                                        ['Barnet', 'Camden', 'Haringey'])
    categorisation_service.add_values_to_categorisation(inner_london,
                                                        ['Camden', 'Haringey'])

    # then the
    greater_london = categorisation_service.get_categorisation('Geography', 'Greater London Boroughs')
    inner_london = categorisation_service.get_categorisation('Geography', 'Inner London Boroughs')
    camden = categorisation_service.create_or_get_value('Camden')

    assert len(camden.categorisations) == 2
    assert len(greater_london.values) == 3
    assert len(inner_london.values) == 2


def test_remove_value_from_category_removes_value(db_session):
    # given a setup with one
    greater_london = categorisation_service.create_categorisation('G1', 'Geography', 'Local level',
                                                                  'Greater London Boroughs')
    inner_london = categorisation_service.create_categorisation('G2', 'Geography', 'Local level',
                                                                'Inner London Boroughs')

    categorisation_service.add_values_to_categorisation(greater_london,
                                                        ['Barnet', 'Camden', 'Haringey'])
    categorisation_service.add_values_to_categorisation(inner_london,
                                                        ['Camden', 'Haringey'])

    # when we remove the value
    categorisation_service.remove_value_from_categorisation(inner_london, 'Camden')

    # then the
    camden = categorisation_service.get_value('Camden')

    assert len(camden.categorisations) == 1
    assert len(greater_london.values) == 3
    assert len(inner_london.values) == 1
    assert 'Inner London Boroughs' not in [c.title for c in camden.categorisations]
    assert 'Camden' not in [c.value for c in inner_london.values]
    assert 'Camden' in [c.value for c in greater_london.values]


def test_add_parent_value_to_category_appends_new_parent(db_session):
    # given a setup with one category
    people = ['Tom', 'Frankie', 'Caroline', 'Adam', 'Cath', 'Marcus', 'Sylvia', 'Katerina']
    rdu = categorisation_service.create_categorisation_with_values('G1', 'People', 'Teams', 'Race Disparity Unit',
                                                                   values=people)
    rdu_by_tribe = categorisation_service.create_categorisation_with_values('G2', 'People', 'Teams',
                                                                            'Race Disparity Unit by Tribe',
                                                                            values=people)
    rdu_by_gender = categorisation_service.create_categorisation_with_values('G3', 'People', 'Teams',
                                                                             'Race Disparity Unit by Gender',
                                                                             values=people)

    # when we link to parents
    categorisation_service.add_values_to_categorisation_as_parents(rdu_by_gender, ['Male', 'Female'])
    categorisation_service.add_values_to_categorisation_as_parents(rdu_by_tribe, ['Data', 'Digital', 'Policy'])

    # then
    standard = categorisation_service.get_categorisation('People', 'Race Disparity Unit')
    by_tribe = categorisation_service.get_categorisation('People', 'Race Disparity Unit by Tribe')
    by_gender = categorisation_service.get_categorisation('People', 'Race Disparity Unit by Gender')
    assert len(standard.parent_values) == 0
    assert len(by_tribe.parent_values) == 3
    assert len(by_gender.parent_values) == 2


def test_remove_parent_value_from_category_removes_value(db_session):
    # given a setup with one category
    people = ['Tom', 'Frankie', 'Caroline', 'Adam', 'Cath', 'Marcus', 'Sylvia', 'Katerina']
    categorisation_service.create_categorisation_with_values('G2', 'People', 'Teams',
                                                             'Race Disparity Unit by Tribe',
                                                             values=people)
    by_tribe = categorisation_service.get_categorisation('People', 'Race Disparity Unit by Tribe')
    categorisation_service.add_values_to_categorisation_as_parents(by_tribe, ['Data', 'Digital', 'Policy'])

    # when
    categorisation_service.remove_parent_value_from_categorisation(by_tribe, 'Digital')

    # then
    by_tribe = categorisation_service.get_categorisation('People', 'Race Disparity Unit by Tribe')
    assert len(by_tribe.parent_values) == 2

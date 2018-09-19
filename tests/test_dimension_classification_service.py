import pytest

from application.cms.classification_service import ClassificationService
from application.cms.dimension_classification_service import DimensionClassificationService, ClassificationLink, \
    DimensionClassificationLink
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Classification, ClassificationValue

dimension_classification_service = DimensionClassificationService()
classification_service = ClassificationService()


def build_ethnicity_classifications():
    classification_service.create_classification_with_values(
        "2A", "Ethnicity", "", "White and other", values=["White", "Other"]
    )
    classification_service.create_classification_with_values(
        "4A", "Ethnicity", "", "HESA", values=["Asian", "Black", "White", "Other including Mixed"]
    )
    classification_service.create_classification_with_values(
        "5A", "Ethnicity", "", "ONS 2011 5+1", values=["Asian", "Black", "Mixed", "White", "Other"]
    )


def build_location_classifications():
    classification_service.create_classification_with_values(
        "A", "Location", "", "Nation", values=["England", "Northern Ireland", "Scotland", "Wales"]
    )
    classification_service.create_classification_with_values(
        "B", "Location", "", "Region", values=["North", "South", "East", "West", "Midlands", "London"]
    )


def test_add_chart_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given an ethnicity classification and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_code("Ethnicity", "2A")

    # when we specify a classification for the dimension's chart
    dimension_classification_service.set_chart_classification_on_dimension(dimension, classification)

    # then a link object is created for the dimension
    assert 1 == dimension.classification_links.count()


def test_add_table_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given an ethnicity classification and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_code("Ethnicity", "2A")

    # when we specify a classification for the dimension's table
    dimension_classification_service.set_table_classification_on_dimension(dimension, classification)

    # then a link object is created for the dimension
    assert 1 == dimension.classification_links.count()


def test_add_chart_classification_to_fresh_does_set_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given an ethnicity classification and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_code("Ethnicity", "2A")

    # when we specify a classification for the dimension's chart
    dimension_classification_service.set_chart_classification_on_dimension(dimension, classification)

    # then a link object is created for the dimension

    dimension_link = DimensionClassificationLink.from_database_object(dimension.classification_links[0])
    assert 1 == dimension.classification_links.count()


def test_dimensions_can_have_more_than_one_linked_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()
    build_location_classifications()

    # given two classifications from different families and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    ethnicity_classification = classification_service.get_classification_by_code("Ethnicity", "2A")
    location_classification = classification_service.get_classification_by_code("Location", "A")

    # when we link them to the dimension
    dimension_classification_service.set_table_classification_on_dimension(dimension, ethnicity_classification)
    dimension_classification_service.set_table_classification_on_dimension(dimension, location_classification)

    # then both categorisations are linked to the dimension
    assert 2 == dimension.classification_links.count()


def test_dimensions_cannot_have_more_that_one_link_per_classification_family(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given two ethnicity classifications and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    ethnicity_classification_1 = classification_service.get_classification_by_code("Ethnicity", "2A")
    ethnicity_classification_2 = classification_service.get_classification_by_code("Ethnicity", "4A")

    # when we link them to the dimension
    dimension_classification_service.set_table_classification_on_dimension(dimension, ethnicity_classification_1)
    dimension_classification_service.set_table_classification_on_dimension(dimension, ethnicity_classification_2)

    # then only one link is counted
    assert 1 == dimension.classification_links.count()


def test_add_more_complex_classification_does_change_main_classification(db_session, stub_page_with_dimension):
    pass


def test_add_less_complex_classification_doesnt_change_main_classification(db_session, stub_page_with_dimension):
    pass


def test_overwrite_most_complex_with_less_can_change_main_classification(db_session, stub_page_with_dimension):
    pass


def test_overwrite_least_complex_with_more_can_change_main_classification(db_session, stub_page_with_dimension):
    pass


def test_delete_least_complex_classification_doesnt_change_main_classification(db_session, stub_page_with_dimension):
    pass


def test_delete_most_complex_classification_changes_main_classification(db_session, stub_page_with_dimension):
    pass


def test_delete_chart_and_table_classification_removes_link_from_database(db_session, stub_page_with_dimension):
    pass

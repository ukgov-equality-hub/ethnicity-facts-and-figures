import pytest

from application.cms.classification_service import ClassificationService
from application.cms.classification_link import ClassificationLink
from application.cms.dimension_classification_service import DimensionClassificationService

from application.cms.exceptions import DimensionClassificationNotFoundException


dimension_classification_service = DimensionClassificationService()
classification_service = ClassificationService()


def build_ethnicity_classifications():
    classification_service.create_classification_with_values("2A", "", "White and other", values=["White", "Other"])
    classification_service.create_classification_with_values(
        "4A", "", "HESA", values=["Asian", "Black", "White", "Other including Mixed"]
    )
    classification_service.create_classification_with_values(
        "5A", "", "ONS 2011 5+1", values=["Asian", "Black", "Mixed", "White", "Other"]
    )


def test_add_chart_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given an ethnicity classification and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_id("2A")

    # when we specify a classification for the dimension's chart
    chart_link = ClassificationLink(classification_id=classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, chart_link)

    # then a link object is created for the dimension
    # assert 1 == dimension.classification_links.count()

    assert "2A" == dimension.dimension_chart.classification_id


def test_add_table_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given an ethnicity classification and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    classification = classification_service.get_classification_by_id("2A")

    # when we specify a classification for the dimension's table
    table_link = ClassificationLink(classification_id=classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, table_link)

    # then a link object is created for the dimension
    assert 1 == dimension.classification_links.count()


def test_dimensions_cannot_have_more_that_one_link_per_classification_family(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given two ethnicity classifications and a dimension
    dimension = stub_page_with_dimension.dimensions[0]
    ethnicity_classification_1 = classification_service.get_classification_by_id("2A")
    ethnicity_classification_2 = classification_service.get_classification_by_id("4A")

    # when we link them to the dimension
    ethnicity_link_1 = ClassificationLink(classification_id=ethnicity_classification_1.id)
    ethnicity_link_2 = ClassificationLink(classification_id=ethnicity_classification_2.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, ethnicity_link_1)
    dimension_classification_service.set_table_classification_on_dimension(dimension, ethnicity_link_2)

    # then only one link is counted
    assert 1 == dimension.classification_links.count()


def test_add_more_complex_chart_does_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to a simple classification via the table
    dimension = stub_page_with_dimension.dimensions[0]
    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, simple_link)

    # when we link a more complex classification via the chart
    complex_classification = classification_service.get_classification_by_id("4A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, complex_link)

    # then the more complex classification is listed as the id
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "4A"


def test_add_more_complex_table_does_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to a simple classification via the chart
    dimension = stub_page_with_dimension.dimensions[0]
    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, simple_link)

    # when we link a more complex classification via the table
    complex_classification = classification_service.get_classification_by_id("4A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)

    # then the more complex classification is listed as the id
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "4A"


def test_add_less_complex_classification_doesnt_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to a complex classification via the table
    dimension = stub_page_with_dimension.dimensions[0]
    complex_classification = classification_service.get_classification_by_id("4A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)

    # when we link a more complex simple via the chart
    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, simple_link)

    # then the original, complex classification is listed as the id
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension, "Ethnicity")
    assert ethnicity_link.main_link.get_classification().id == "4A"


def test_overwrite_most_complex_with_less_can_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to 5 categories on table and 4 on chart
    dimension = stub_page_with_dimension.dimensions[0]
    complex_classification = classification_service.get_classification_by_id("5A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)
    medium_classification = classification_service.get_classification_by_id("4A")
    medium_link = ClassificationLink(classification_id=medium_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, medium_link)

    # then the complex classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "5A"

    # when we swap out the 5A for a 2A
    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, simple_link)

    # then the mid-level classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "4A"


def test_overwrite_least_complex_with_more_can_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to 2 categories on table and 4 on chart
    dimension = stub_page_with_dimension.dimensions[0]
    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, simple_link)

    medium_classification = classification_service.get_classification_by_id("4A")
    medium_link = ClassificationLink(classification_id=medium_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, medium_link)

    # then the complex classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "4A"

    # when we swap out the simple classification for a five level
    complex_classification = classification_service.get_classification_by_id("5A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)

    # then the mid-level classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "5A"


def test_delete_least_complex_classification_doesnt_change_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to 5 categories on table and 2 on chart
    dimension = stub_page_with_dimension.dimensions[0]
    complex_classification = classification_service.get_classification_by_id("5A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)

    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, simple_link)

    # then the complex classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "5A"

    # when we delete the simple classification
    dimension_classification_service.remove_chart_classification_on_dimension(dimension)

    # then the complex classification is still listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "5A"


def test_delete_most_complex_classification_changes_main_classification(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to 5 categories on table and 2 on chart
    dimension = stub_page_with_dimension.dimensions[0]
    complex_classification = classification_service.get_classification_by_id("5A")
    complex_link = ClassificationLink(classification_id=complex_classification.id)
    dimension_classification_service.set_table_classification_on_dimension(dimension, complex_link)

    simple_classification = classification_service.get_classification_by_id("2A")
    simple_link = ClassificationLink(classification_id=simple_classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, simple_link)

    # then the complex classification is listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "5A"

    # when we delete the complex classification
    dimension_classification_service.remove_table_classification_on_dimension(dimension)

    # then the complex classification is still listed as the main link
    ethnicity_link = dimension_classification_service.get_dimension_classification_link(dimension)
    assert ethnicity_link.main_link.get_classification().id == "2A"


def test_delete_chart_and_table_classification_removes_link_from_database(db_session, stub_page_with_dimension):
    build_ethnicity_classifications()

    # given a dimension linked to categories on table and on chart
    dimension = stub_page_with_dimension.dimensions[0]

    classification = classification_service.get_classification_by_id("5A")
    link = ClassificationLink(classification_id=classification.id)
    dimension_classification_service.set_chart_classification_on_dimension(dimension, link)
    dimension_classification_service.set_table_classification_on_dimension(dimension, link)

    # when we delete both classifications
    dimension_classification_service.remove_table_classification_on_dimension(dimension)
    dimension_classification_service.remove_chart_classification_on_dimension(dimension)

    # then the classification link has been deleted
    with pytest.raises(DimensionClassificationNotFoundException):
        dimension_classification_service.get_dimension_classification_link(dimension)

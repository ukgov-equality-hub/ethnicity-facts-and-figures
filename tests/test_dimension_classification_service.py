import pytest

from application.cms.classification_service import ClassificationService
from application.cms.dimension_classification_service import DimensionClassificationService, ClassificationLink
from application.cms.exceptions import ClassificationNotFoundException
from application.cms.models import Classification, ClassificationValue

dimension_classification_service = DimensionClassificationService()
classification_service = ClassificationService()


def build_ethnicity_classifications():
    classification_service.create_classification_with_values(
        "2A", "Ethnicity", "", "White and other", values=["White", "Other"]
    )
    classification_service.create_classification_with_values(
        "5A", "Ethnicity", "", "ONS 2011 5+1", values=["Asian", "Black", "Mixed", "White", "Other"]
    )


def build_location_classifications():
    classification_service.create_classification_with_values(
        "4A", "Location", "", "Countries", values=["England", "Ireland", "Scotland", "Wales"]
    )
    classification_service.create_classification_with_values(
        "5A", "Location", "", "Regions", values=["North", "South", "East", "West"]
    )


def test_add_chart_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    pass


def test_add_table_classification_to_fresh_dimension_does_save(db_session, stub_page_with_dimension):
    pass


def test_dimensions_cannot_have_more_that_one_link_per_classification_family(db_session, stub_page_with_dimension):
    pass


def test_dimensions_can_have_one_link_per_classification_family(db_session, stub_page_with_dimension):
    pass


def test_dimensions_save_links_to_one_database_entry_per_classification_family(db_session, stub_page_with_dimension):
    pass


def test_add_more_complex_classification_does_overwrite(db_session, stub_page_with_dimension):
    pass


def test_add_less_complex_classification_doesnt_overwrite(db_session, stub_page_with_dimension):
    pass


def test_delete_least_complex_table_classification_doesnt_overwrite(db_session, stub_page_with_dimension):
    pass


def test_delete_most_complex_table_classification_does_overwrite(db_session, stub_page_with_dimension):
    pass

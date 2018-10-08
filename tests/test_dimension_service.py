from application.cms.models import Dimension
from application.cms.dimension_service import DimensionService

dimension_service = DimensionService()


def test_create_dimension_on_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid
    assert stub_measure_page.dimensions[0].title == db_dimension.title


def test_delete_dimension_from_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid

    dimension_service.delete_dimension(stub_measure_page, db_dimension.guid)
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0


def test_update_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    update_data = {"title": "updated-title", "time_period": "updated_time_period"}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.title == "updated-title"
    assert updated_dimension.time_period == "updated_time_period"


def test_add_chart_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    chart = {"chart_is_just_a": "dictionary"}

    update_data = {"chart": chart}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.chart
    assert updated_dimension.chart == chart


def test_add_table_to_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    table = {"table_is_just_a": "dictionary"}

    update_data = {"table": table}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.table
    assert updated_dimension.table == table


def test_adding_table_with_data_custom_matching_an_ethnicity_classification(stub_measure_page):

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    # When update_dimension is called with table data and a matching
    # classification
    update_data = {
        "use_custom": True,
        "table": {"title": "My table title"},
        "table_2_source_data": {"tableOptions": {}},
        "classification_code": "2A",
        "has_parents": True,
        "has_all": True,
        "has_unknown": True,
    }

    dimension_service.update_dimension(dimension, update_data)

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.get(dimension.id)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    assert dimension.dimension_table != None
    assert dimension.dimension_table.classification_code == "2A"
    assert dimension.dimension_table.includes_parents == True
    assert dimension.dimension_table.includes_all == True
    assert dimension.dimension_table.includes_unknown == True


def test_delete_chart_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    chart = {"chart_is_just_a": "dictionary"}
    update_data = {"chart": chart}
    dimension_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.chart

    dimension_service.delete_chart(updated_dimension)
    assert not updated_dimension.chart


def test_delete_table_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    table = {"table_is_just_a": "dictionary"}
    update_data = {"table": table}
    dimension_service.update_dimension(dimension, update_data)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.table

    dimension_service.delete_table(updated_dimension)
    assert not updated_dimension.table


def test_add_or_update_dimensions_to_measure_page_preserves_order(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    d1 = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension-1",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    d2 = dimension_service.create_dimension(
        stub_measure_page,
        title="test-dimension-2",
        time_period="time_period",
        summary="summary",
        ethnicity_classification_id="",
    )

    assert stub_measure_page.dimensions[0].title == d1.title
    assert d1.position == 0
    assert stub_measure_page.dimensions[0].position == d1.position

    assert stub_measure_page.dimensions[1].title == "test-dimension-2"
    assert d2.position == 1
    assert stub_measure_page.dimensions[1].position == d2.position

    # after update. positions should not have changed
    dimension_service.update_dimension(d1, {"summary": "updated summary"})
    assert d1.summary == "updated summary"
    assert d1.position == 0
    assert d2.position == 1

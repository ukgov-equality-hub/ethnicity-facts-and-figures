from application.cms.models import Dimension
from application.cms.dimension_service import DimensionService
from application.cms.classification_service import ClassificationService
from application.cms.models import Dimension, Chart, Table, DimensionClassification
from application import db

dimension_service = DimensionService()


def test_create_dimension_on_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    db_dimension = Dimension.query.all()[0]
    assert stub_measure_page.dimensions[0].guid == db_dimension.guid
    assert stub_measure_page.dimensions[0].title == db_dimension.title


def test_delete_dimension_from_measure_page(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
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
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
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
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
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
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    table = {"table_is_just_a": "dictionary"}

    update_data = {"table": table}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = stub_measure_page.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.table
    assert updated_dimension.table == table


def test_adding_table_with_data_matching_an_ethnicity_classification(stub_measure_page):

    # Given an existing classification with code '2A'
    ClassificationService().create_classification("5A", "", "Test classification")

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with table data and a matching
    # classification with code '2A'
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": False,
            "table": {"title": "My table title"},
            "table_2_source_data": {"tableOptions": {}},
            "classification_code": "5A",
            "ethnicity_values": ["All", "Asian", "Black", "Mixed", "White", "Other", "Unknown"],
        },
    )

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    assert dimension.dimension_table != None
    assert dimension.dimension_table.classification_id == "5A"
    assert dimension.dimension_table.includes_parents is False
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True


def test_adding_chart_with_data_matching_an_ethnicity_classification(stub_measure_page):

    # Given an existing classification with code '2A'
    ClassificationService().create_classification("5A", "", "Test classification")

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with chart data and a matching
    # classification with code '2A', but use_custom is False
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": False,
            "chart": {"title": "My chart title"},
            "chart_2_source_data": {"chartOptions": {}},
            "classification_code": "5A",
            "ethnicity_values": ["All", "Asian", "Black", "Mixed", "White", "Other", "Unknown"],
        },
    )

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    assert dimension.dimension_chart != None
    assert dimension.dimension_chart.classification_id == "5A"
    assert dimension.dimension_chart.includes_parents is False
    assert dimension.dimension_chart.includes_all is True
    assert dimension.dimension_chart.includes_unknown is True


def test_adding_table_with_custom_data(stub_measure_page):

    # Given an existing classification with code '2A'
    ClassificationService().create_classification("2A", "", "Test classification")

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with table data and a matching
    # classification with code '2A'
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": True,
            "table": {"title": "My table title"},
            "table_2_source_data": {"tableOptions": {}},
            "classification_code": "2A",
            "has_parents": True,
            "has_all": True,
            "has_unknown": True,
        },
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    # An associated Table should be created with the metadata given
    assert dimension.dimension_table != None
    assert dimension.dimension_table.classification_id == "2A"
    assert dimension.dimension_table.includes_parents is True
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True

    # And the dimension itself should have the same metadata values as there’s no chart
    assert dimension.dimension_classification != None
    assert dimension.dimension_classification.classification_id == "2A"
    assert dimension.dimension_classification.includes_parents == True
    assert dimension.dimension_classification.includes_all == True
    assert dimension.dimension_classification.includes_unknown == True


def test_adding_table_with_custom_data_and_existing_more_detailed_chart(stub_measure_page):

    # Given an existing classification with code '2A'
    ClassificationService().create_classification("2A", "", "Simple classification")

    # And an existing classification with code '10A'
    ClassificationService().create_classification("10A", "", "More detailed classification")

    # And an existing dimension with a chart but no table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    dimension.table = {"table_is_just_a": "dictionary"}
    dimension.table_source_data = {"values": 1}
    dimension.table_2_source_data = {"values": 2}

    chart = Chart()
    chart.classification_id = "10A"
    chart.includes_parents = True
    chart.includes_all = False
    chart.includes_unknown = False

    db.session.add(chart)
    db.session.commit()

    dimension.dimension_chart = chart

    # When update_dimension is called with table data and a matching
    # classification with code '2A'
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": True,
            "table": {"title": "My table title"},
            "table_2_source_data": {"tableOptions": {}},
            "classification_code": "2A",
            "has_parents": True,
            "has_all": True,
            "has_unknown": True,
        },
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    # An associated Table should be created with the metadata given
    assert dimension.dimension_table != None
    assert dimension.dimension_table.classification_id == "2A"
    assert dimension.dimension_table.includes_parents is True
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True

    # And the dimension itself should have the same metadata as the chart
    assert dimension.dimension_classification != None
    assert dimension.dimension_classification.classification_id == "10A"
    assert dimension.dimension_classification.includes_parents == True
    assert dimension.dimension_classification.includes_all == False
    assert dimension.dimension_classification.includes_unknown == False


def test_adding_chart_with_data_custom_matching_an_ethnicity_classification(stub_measure_page):

    # Given an existing classification with code '2A'
    ClassificationService().create_classification("2A", "", "Test classification")

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with table data and a matching
    # classification with code '2A'
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": True,
            "chart": {"title": "My chart title"},
            "chart_2_source_data": {"chartOptions": {}},
            "classification_code": "2A",
            "has_parents": True,
            "has_all": True,
            "has_unknown": True,
        },
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The chart and chart_2_source_data objects get passed straight to the database
    assert dimension.chart == {"title": "My chart title"}
    assert dimension.chart_2_source_data == {"chartOptions": {}}

    # An associated Chart should be created with the metadata given
    assert dimension.dimension_chart != None
    assert dimension.dimension_chart.classification_id == "2A"
    assert dimension.dimension_chart.includes_parents is True
    assert dimension.dimension_chart.includes_all is True
    assert dimension.dimension_chart.includes_unknown is True

    # TODO: And the dimension itself should have the same metadata values
    # assert dimension.classification_id == "2A"
    # assert dimension.includes_parents == True
    # assert dimension.includes_all == True
    # assert dimension.includes_unknown == True


def test_delete_chart_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    ClassificationService().create_classification("3B", "", "Test classification")

    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    chart = Chart()
    chart.classification_id = "3B"
    chart.includes_parents = False
    chart.includes_all = False
    chart.includes_unknown = True

    db.session.add(chart)
    db.session.commit()

    dimension.chart = {"chart_is_just_a": "dictionary"}
    dimension.chart_source_data = {"values": 1}
    dimension.chart_2_source_data = {"values": 2}

    dimension.dimension_chart = chart

    db.session.add(dimension)
    db.session.commit()

    # When the chart is deleted
    dimension_service.delete_chart(dimension)

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # Then the chart attributes should have been removed
    assert dimension.chart is None
    assert dimension.chart_source_data is None
    assert dimension.chart_2_source_data is None

    # And the associated chart object should have been removed
    assert dimension.dimension_chart is None


def test_delete_table_from_dimension(stub_measure_page):
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    ClassificationService().create_classification("2A", "", "Test classification")

    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    dimension.table = {"table_is_just_a": "dictionary"}
    dimension.table_source_data = {"values": 1}
    dimension.table_2_source_data = {"values": 2}

    table = Table()
    table.classification_id = "2A"
    table.includes_parents = True
    table.includes_all = False
    table.includes_unknown = False

    db.session.add(table)
    db.session.commit()

    dimension.dimension_table = table

    db.session.add(dimension)
    db.session.commit()

    # When I delete a table
    dimension_service.delete_table(dimension)

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # Then it should have removed all the table data
    assert dimension.table is None
    assert dimension.table_source_data is None
    assert dimension.table_2_source_data is None

    # And the associated table metadata
    assert dimension.dimension_table is None


def test_add_or_update_dimensions_to_measure_page_preserves_order(stub_measure_page):

    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    d1 = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension-1", time_period="time_period", summary="summary"
    )

    d2 = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension-2", time_period="time_period", summary="summary"
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

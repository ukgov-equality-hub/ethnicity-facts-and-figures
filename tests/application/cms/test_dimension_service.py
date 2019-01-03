from application.cms.dimension_service import DimensionService
from application.cms.models import Chart, Dimension, DimensionClassification
from application import db
from datetime import datetime

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
    assert stub_measure_page.dimensions[0].created_at is not None, "Should have set a creation timestamp"

    assert (
        datetime.utcnow() - stub_measure_page.dimensions[0].created_at
    ).seconds < 5, "Creation time should be within the last 5 seconds"

    assert (
        stub_measure_page.dimensions[0].updated_at == stub_measure_page.dimensions[0].created_at
    ), "Should have set the updated timestamp to be the same as the creation timestamp"


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

    assert (
        updated_dimension.updated_at != updated_dimension.created_at
    ), "Update time should now be different from creation time"

    assert (
        datetime.utcnow() - updated_dimension.updated_at
    ).seconds < 5, "Update time should be within the last 5 seconds"


def test_update_dimension_does_not_call_update_dimension_classification_by_default(
    stub_measure_page, two_classifications_2A_5A
):
    # Given a dimension with some metadata
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # And a classification
    assert dimension.dimension_classification is None
    dimension_classification = DimensionClassification()
    dimension_classification.dimension_guid = dimension.guid
    dimension_classification.classification_id = "5A"
    dimension_classification.includes_parents = False
    dimension_classification.includes_all = True
    dimension_classification.includes_unknown = True
    db.session.add(dimension_classification)
    db.session.commit()
    assert dimension.dimension_classification is not None

    # When update_dimension() is called without explicitly telling it to reclassify the dimension
    update_data = {"title": "updated-title", "time_period": "updated_time_period"}
    dimension_service.update_dimension(dimension, update_data)

    # Then the dimension classification should not have been overwritten/deleted
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.dimension_classification is not None
    assert updated_dimension.dimension_classification.classification_id == "5A"
    assert updated_dimension.dimension_classification.includes_parents is False
    assert updated_dimension.dimension_classification.includes_all is True
    assert updated_dimension.dimension_classification.includes_unknown is True


def test_update_dimension_does_call_update_dimension_classification_if_told_to(
    stub_measure_page, two_classifications_2A_5A
):
    # Given a dimension with some metadata
    assert not Dimension.query.all()
    assert stub_measure_page.dimensions.count() == 0

    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # And a classification
    assert dimension.dimension_classification is None
    dimension_classification = DimensionClassification()
    dimension_classification.dimension_guid = dimension.guid
    dimension_classification.classification_id = "5A"
    dimension_classification.includes_parents = False
    dimension_classification.includes_all = True
    dimension_classification.includes_unknown = True
    db.session.add(dimension_classification)
    db.session.commit()
    assert dimension.dimension_classification is not None

    # When update_dimension() is called without explicitly telling it to reclassify the dimension
    update_data = {"title": "updated-title", "time_period": "updated_time_period"}
    dimension_service.update_dimension(dimension, update_data, update_classification=True)

    # Then the dimension classification should have been overwritten/deleted
    # (in this case deleted as there is no associated chart or table object)
    updated_dimension = stub_measure_page.dimensions[0]
    assert updated_dimension.dimension_classification is None


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


def test_adding_table_with_data_matching_an_ethnicity_classification(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with table data with classification code '5A' and use_custom False
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": False,
            "table": {"title": "My table title"},
            "table_2_source_data": {"tableOptions": {}},
            "classification_code": "5A",
            "ethnicity_values": ["All", "Asian", "Black", "Mixed", "White", "Other", "Unknown"],
        },
        update_classification=True,
    )

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # Then the classification is set on dimension_table with flags calculated from ethnicity_values
    assert dimension.dimension_table is not None
    assert dimension.dimension_table.classification_id == "5A"
    assert dimension.dimension_table.includes_parents is False
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True


def test_adding_chart_with_data_matching_an_ethnicity_classification(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with no associated chart
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with chart data with classification code '2A' and use_custom False
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": False,
            "chart": {"title": "My chart title"},
            "chart_2_source_data": {"chartOptions": {}},
            "classification_code": "5A",
            "ethnicity_values": ["All", "Asian", "Black", "Mixed", "White", "Other", "Unknown"],
        },
        update_classification=True,
    )

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # Then the classification is set on dimension_chart with flags calculated from ethnicity_values
    assert dimension.dimension_chart is not None
    assert dimension.dimension_chart.classification_id == "5A"
    assert dimension.dimension_chart.includes_parents is False
    assert dimension.dimension_chart.includes_all is True
    assert dimension.dimension_chart.includes_unknown is True


def test_adding_table_with_custom_data_classification(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with table data with classification code '2A' and use_custom True
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
        update_classification=True,
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    # An associated Table should be created with the metadata given
    assert dimension.dimension_table is not None
    assert dimension.dimension_table.classification_id == "2A"
    assert dimension.dimension_table.includes_parents is True
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True

    # And the dimension itself should have the same metadata values as there’s no chart
    assert dimension.dimension_classification is not None
    assert dimension.dimension_classification.classification_id == "2A"
    assert dimension.dimension_classification.includes_parents is True
    assert dimension.dimension_classification.includes_all is True
    assert dimension.dimension_classification.includes_unknown is True


def test_adding_chart_with_custom_data_classification(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with no associated table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    # When update_dimension is called with chart data with classification code '2A' and use_custom True
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
        update_classification=True,
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The chart and chart_2_source_data objects get passed straight to the database
    assert dimension.chart == {"title": "My chart title"}
    assert dimension.chart_2_source_data == {"chartOptions": {}}

    # An associated Chart should be created with the metadata given
    assert dimension.dimension_chart is not None
    assert dimension.dimension_chart.classification_id == "2A"
    assert dimension.dimension_chart.includes_parents is True
    assert dimension.dimension_chart.includes_all is True
    assert dimension.dimension_chart.includes_unknown is True

    # And the dimension itself should have the same metadata values as there’s no table
    assert dimension.dimension_classification is not None
    assert dimension.dimension_classification.classification_id == "2A"
    assert dimension.dimension_classification.includes_parents is True
    assert dimension.dimension_classification.includes_all is True
    assert dimension.dimension_classification.includes_unknown is True


def test_adding_table_with_custom_data_and_existing_more_detailed_chart(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with a chart with classification '5A' but no table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    dimension.chart = {"chart_is_just_a": "dictionary"}
    dimension.chart_source_data = {"values": 1}
    dimension.chart_2_source_data = {"values": 2}

    chart = Chart()
    chart.classification_id = "5A"
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
        update_classification=True,
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    # An associated Table should be created with the metadata given
    assert dimension.dimension_table is not None
    assert dimension.dimension_table.classification_id == "2A"
    assert dimension.dimension_table.includes_parents is True
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True

    # And the dimension itself should have the same metadata as the chart
    assert dimension.dimension_classification is not None
    assert dimension.dimension_classification.classification_id == "5A"
    assert dimension.dimension_classification.includes_parents is True
    assert dimension.dimension_classification.includes_all is False
    assert dimension.dimension_classification.includes_unknown is False


def test_adding_table_with_custom_data_and_existing_less_detailed_chart(stub_measure_page, two_classifications_2A_5A):

    # Given an existing dimension with a chart with classification '2A' but no table
    dimension = dimension_service.create_dimension(
        stub_measure_page, title="test-dimension", time_period="time_period", summary="summary"
    )

    dimension.chart = {"chart_is_just_a": "dictionary"}
    dimension.chart_source_data = {"values": 1}
    dimension.chart_2_source_data = {"values": 2}

    chart = Chart()
    chart.classification_id = "2A"
    chart.includes_parents = True
    chart.includes_all = False
    chart.includes_unknown = False

    db.session.add(chart)
    db.session.commit()

    dimension.dimension_chart = chart

    # When update_dimension is called with table data and a matching
    # classification with code '5A'
    dimension_service.update_dimension(
        dimension,
        {
            "use_custom": True,
            "table": {"title": "My table title"},
            "table_2_source_data": {"tableOptions": {}},
            "classification_code": "5A",
            "has_parents": False,
            "has_all": True,
            "has_unknown": True,
        },
        update_classification=True,
    )

    # Then it should set the table and associated metadata

    # refresh the dimension from the database
    dimension = Dimension.query.get(dimension.guid)

    # The table and table_2_source_data objects get passed straight to the database
    assert dimension.table == {"title": "My table title"}
    assert dimension.table_2_source_data == {"tableOptions": {}}

    # An associated Table should be created with the metadata given
    assert dimension.dimension_table is not None
    assert dimension.dimension_table.classification_id == "5A"
    assert dimension.dimension_table.includes_parents is False
    assert dimension.dimension_table.includes_all is True
    assert dimension.dimension_table.includes_unknown is True

    # And the dimension itself should have the same metadata as the newly saved table
    assert dimension.dimension_classification is not None
    assert dimension.dimension_classification.classification_id == "5A"
    assert dimension.dimension_classification.includes_parents is False
    assert dimension.dimension_classification.includes_all is True
    assert dimension.dimension_classification.includes_unknown is True


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

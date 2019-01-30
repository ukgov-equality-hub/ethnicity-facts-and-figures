from datetime import datetime

from application import db
from application.cms.dimension_service import DimensionService
from application.cms.models import Chart, Dimension
from tests.models import MeasureVersionFactory, MeasureVersionWithDimensionFactory

dimension_service = DimensionService()


def test_create_dimension_on_measure_page():
    measure_version = MeasureVersionFactory()
    assert measure_version.dimensions.count() == 0

    dimension_service.create_dimension(
        measure_version, title="test-dimension", time_period="time_period", summary="summary"
    )

    assert measure_version.dimensions.count() == 1
    assert measure_version.dimensions[0].title == "test-dimension"
    assert measure_version.dimensions[0].time_period == "time_period"
    assert measure_version.dimensions[0].summary == "summary"
    assert measure_version.dimensions[0].created_at is not None, "Should have set a creation timestamp"

    assert (
        datetime.utcnow() - measure_version.dimensions[0].created_at
    ).seconds < 5, "Creation time should be within the last 5 seconds"

    assert (
        measure_version.dimensions[0].updated_at == measure_version.dimensions[0].created_at
    ), "Should have set the updated timestamp to be the same as the creation timestamp"


def test_delete_dimension_from_draft_measure_page():
    measure_version = MeasureVersionWithDimensionFactory(status="DRAFT", dimensions__guid="abc123")

    assert measure_version.dimensions.count() == 1
    assert measure_version.dimensions[0].guid == "abc123"

    dimension_service.delete_dimension(measure_version, "abc123")

    assert measure_version.dimensions.count() == 0


def test_update_dimension():
    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="test dimension", dimensions__time_period="time period", dimensions__summary="summary"
    )
    dimension = measure_version.dimensions[0]

    update_data = {"title": "updated-title", "time_period": "updated_time_period"}

    dimension_service.update_dimension(dimension, update_data)

    updated_dimension = measure_version.dimensions[0]
    assert dimension.guid == updated_dimension.guid
    assert updated_dimension.title == "updated-title"
    assert updated_dimension.time_period == "updated_time_period"

    assert (
        updated_dimension.updated_at != updated_dimension.created_at
    ), "Update time should now be different from creation time"

    assert (
        datetime.utcnow() - updated_dimension.updated_at
    ).seconds < 5, "Update time should be within the last 5 seconds"


def test_update_dimension_does_not_call_update_dimension_classification_by_default():
    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="test-dimension",
        dimensions__time_period="time_period",
        dimensions__summary="summary",
        dimensions__classification_links__includes_parents=False,
        dimensions__classification_links__includes_all=True,
        dimensions__classification_links__includes_unknown=True,
        dimensions__classification_links__classification__id="my-classification",
    )

    dimension = measure_version.dimensions[0]
    assert measure_version.dimensions.count() == 1
    assert dimension.title == "test-dimension"
    assert dimension.time_period == "time_period"
    assert dimension.summary == "summary"
    assert dimension.dimension_classification.classification_id == "my-classification"
    assert dimension.dimension_classification.includes_parents is False
    assert dimension.dimension_classification.includes_all is True
    assert dimension.dimension_classification.includes_unknown is True

    # When update_dimension() is called without explicitly telling it to reclassify the dimension
    update_data = {"title": "updated-title", "time_period": "updated_time_period"}
    dimension_service.update_dimension(dimension, update_data)

    # Then the dimension classification should not have been overwritten/deleted
    assert dimension.title == "updated-title"
    assert dimension.time_period == "updated_time_period"
    assert dimension.summary == "summary"
    assert dimension.dimension_classification.classification_id == "my-classification"
    assert dimension.dimension_classification.includes_parents is False
    assert dimension.dimension_classification.includes_all is True
    assert dimension.dimension_classification.includes_unknown is True


def test_update_dimension_does_call_update_dimension_classification_if_told_to():
    measure_version = MeasureVersionWithDimensionFactory(
        dimensions__title="test-dimension",
        dimensions__time_period="time_period",
        dimensions__summary="summary",
        dimensions__dimension_chart=None,
        dimensions__dimension_table=None,
    )

    dimension = measure_version.dimensions[0]
    assert measure_version.dimensions.count() == 1
    assert dimension.dimension_classification is not None

    # When update_dimension() is called without explicitly telling it to reclassify the dimension
    update_data = {"title": "updated-title", "time_period": "updated_time_period"}
    dimension_service.update_dimension(dimension, update_data, update_classification=True)

    # Then the dimension classification should have been overwritten/deleted
    # (in this case deleted as there is no associated chart or table object)
    assert dimension.dimension_classification is None


def test_add_chart_to_dimension():
    measure_version = MeasureVersionWithDimensionFactory(dimensions__guid="abc123", dimensions__dimension_chart=None)
    dimension = measure_version.dimensions[0]
    chart = {"chart_is_just_a": "dictionary"}

    assert dimension.guid == "abc123"
    assert dimension.chart is None

    dimension_service.update_dimension(measure_version.dimensions[0], {"chart": chart})

    assert dimension.guid == "abc123"
    assert dimension.chart == chart


def test_add_table_to_dimension():
    measure_version = MeasureVersionWithDimensionFactory(dimensions__guid="abc123", dimensions__dimension_table=None)
    dimension = measure_version.dimensions[0]
    table = {"table_is_just_a": "dictionary"}

    assert dimension.guid == "abc123"
    assert dimension.table is None

    dimension_service.update_dimension(dimension, {"table": table})

    assert dimension.guid == "abc123"
    assert dimension.table == table


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


def test_add_or_update_dimensions_to_measure_page_preserves_order():
    measure_version = MeasureVersionFactory()

    assert measure_version.dimensions.count() == 0

    d1 = dimension_service.create_dimension(
        measure_version, title="test-dimension-1", time_period="time_period", summary="summary"
    )

    d2 = dimension_service.create_dimension(
        measure_version, title="test-dimension-2", time_period="time_period", summary="summary"
    )

    assert measure_version.dimensions[0].title == d1.title
    assert d1.position == 0
    assert measure_version.dimensions[0].position == d1.position

    assert measure_version.dimensions[1].title == "test-dimension-2"
    assert d2.position == 1
    assert measure_version.dimensions[1].position == d2.position

    # after update. positions should not have changed
    dimension_service.update_dimension(d1, {"summary": "updated summary"})
    assert d1.summary == "updated summary"
    assert d1.position == 0
    assert d2.position == 1

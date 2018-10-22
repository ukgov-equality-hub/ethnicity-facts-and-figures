from application.cms.models import Dimension


class TestDimensionModel:
    def test_copy_dimension_makes_copies_of_chart_and_table(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_fixture_guid = dimension_fixture.guid
        original_chart_id = dimension_fixture.chart_id
        original_table_id = dimension_fixture.table_id

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension_fixture.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension_fixture = Dimension.query.filter(Dimension.guid == dimension_fixture_guid).one()

        # The copied dimension has a new Chart attached to it
        assert copied_dimension.dimension_chart is not None
        assert copied_dimension.chart_id != original_chart_id
        # The original dimension still has the old chart
        assert dimension_fixture.chart_id == original_chart_id
        # The copied Chart is the same as the original Chart
        assert copied_dimension.dimension_chart.classification_id == dimension_fixture.dimension_chart.classification_id
        assert copied_dimension.dimension_chart.includes_all == dimension_fixture.dimension_chart.includes_all
        assert copied_dimension.dimension_chart.includes_parents == dimension_fixture.dimension_chart.includes_parents
        assert copied_dimension.dimension_chart.includes_unknown == dimension_fixture.dimension_chart.includes_unknown

        # The copied dimension has a new Table attached to it
        assert copied_dimension.dimension_table is not None
        assert copied_dimension.table_id != original_table_id
        # The original dimension still has the old table
        assert dimension_fixture.table_id == original_table_id
        # The copied Table is the same as the original Table
        assert copied_dimension.dimension_table.classification_id == dimension_fixture.dimension_table.classification_id
        assert copied_dimension.dimension_table.includes_all == dimension_fixture.dimension_table.includes_all
        assert copied_dimension.dimension_table.includes_parents == dimension_fixture.dimension_table.includes_parents
        assert copied_dimension.dimension_table.includes_unknown == dimension_fixture.dimension_table.includes_unknown

    def test_copy_dimension_can_copy_dimensions_without_chart_or_table(self, db_session, stub_page_with_dimension):
        dimension_fixture = Dimension.query.one()
        dimension_fixture_guid = dimension_fixture.guid
        original_chart_id = dimension_fixture.chart_id
        original_table_id = dimension_fixture.table_id

        # The dimension has no chart or table to start with
        assert original_chart_id is None
        assert original_table_id is None

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension_fixture.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension_fixture = Dimension.query.filter(Dimension.guid == dimension_fixture_guid).one()

        # Both the original and copied dimensions have no Chart or Table
        assert dimension_fixture.dimension_chart is None
        assert copied_dimension.chart_id is None
        assert copied_dimension.dimension_chart is None

        assert dimension_fixture.dimension_table is None
        assert copied_dimension.table_id is None
        assert copied_dimension.dimension_table is None

    def test_copy_dimension_can_copy_dimensions_with_one_chart_or_table(
        self, db_session, stub_page_with_dimension_and_chart
    ):
        dimension_fixture = Dimension.query.one()
        dimension_fixture_guid = dimension_fixture.guid
        original_chart_id = dimension_fixture.chart_id
        original_table_id = dimension_fixture.table_id

        # The dimension has no table to start with
        assert original_table_id is None

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension_fixture.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension_fixture = Dimension.query.filter(Dimension.guid == dimension_fixture_guid).one()

        # The copied dimension has a new Chart attached to it
        assert copied_dimension.dimension_chart is not None
        assert copied_dimension.chart_id != original_chart_id
        # The original dimension still has the old chart
        assert dimension_fixture.chart_id == original_chart_id
        # The copied Chart is the same as the original Chart
        assert copied_dimension.dimension_chart.classification_id == dimension_fixture.dimension_chart.classification_id
        assert copied_dimension.dimension_chart.includes_all == dimension_fixture.dimension_chart.includes_all
        assert copied_dimension.dimension_chart.includes_parents == dimension_fixture.dimension_chart.includes_parents
        assert copied_dimension.dimension_chart.includes_unknown == dimension_fixture.dimension_chart.includes_unknown

        # Both the original and copied dimensions have no Table
        assert dimension_fixture.dimension_table is None
        assert copied_dimension.table_id is None
        assert copied_dimension.dimension_table is None

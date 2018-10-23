import pytest

from application.cms.models import Dimension, DimensionClassification


class TestDimensionModel:
    def test_classification_source_string_is_none_if_no_dimension_classification(
        self, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_fixture.dimension_table = None
        dimension_fixture.dimension_chart = None
        assert dimension_fixture.classification_source_string is None

    def test_classification_source_string_is_manually_selected_if_no_chart_or_table_classification(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="5A",
            includes_parents=False,
            includes_all=False,
            includes_unknown=False,
        )
        db_session.session.add(dimension_classification)
        db_session.session.commit()
        dimension_fixture.dimension_table = None
        dimension_fixture.dimension_chart = None
        assert dimension_fixture.classification_source_string == "Manually selected"

    def test_classification_source_string_is_manually_selected_if_no_match_with_chart_or_table_classification(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="5A",
            includes_parents=False,
            includes_all=False,
            includes_unknown=False,
        )
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        # So neither match the dimension_classification
        assert dimension_fixture.classification_source_string == "Manually selected"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_and_no_table(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_fixture.dimension_table = None
        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="2A",
            includes_parents=False,
            includes_all=True,
            includes_unknown=False,
        )
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        assert dimension_fixture.classification_source_string == "Chart"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_but_not_with_table(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="2A",
            includes_parents=False,
            includes_all=True,
            includes_unknown=False,
        )
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        assert dimension_fixture.classification_source_string == "Chart"

    def test_classification_source_string_is_table_if_match_with_table_classification_but_not_with_chart(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="5A",
            includes_parents=True,
            includes_all=False,
            includes_unknown=True,
        )
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        assert dimension_fixture.classification_source_string == "Table"

    def test_classification_source_string_is_table_if_match_with_both_table_and_chart_classification(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        dimension_classification = DimensionClassification(
            dimension_guid=dimension_fixture.guid,
            classification_id="2A",
            includes_parents=False,
            includes_all=True,
            includes_unknown=False,
        )
        # Update dimension_table classification to also match
        dimension_fixture.dimension_table.classification_id = "2A"
        dimension_fixture.dimension_table.includes_parents = False
        dimension_fixture.dimension_table.includes_all = True
        dimension_fixture.dimension_table.includes_unknown = False

        db_session.session.add(dimension_classification)
        db_session.session.add(dimension_fixture)
        db_session.session.commit()

        assert dimension_fixture.classification_source_string == "Table"

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

    def test_copy_dimension_copies_classification_links(self):
        pass

    def test_update_dimension_classification_from_chart_or_table_does_the_right_thing(self):
        pass

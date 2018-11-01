from application.cms.models import Dimension, DimensionClassification


class TestDimensionModel:
    def test_classification_source_string_is_none_if_no_dimension_classification(
        self, stub_page_with_dimension, two_classifications_2A_5A
    ):
        dimension_fixture = Dimension.query.one()
        assert dimension_fixture.classification_source_string is None

    def test_classification_source_string_is_manually_selected_if_no_chart_or_table_classification(
        self, db_session, stub_page_with_dimension, two_classifications_2A_5A
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
        assert dimension_fixture.classification_source_string == "Manually selected"

    def test_classification_source_string_is_manually_selected_if_no_match_with_chart_or_table_classification(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_classification = DimensionClassification.query.one()
        # Update the classification to *NOT* match that of the table that currently set classification is based on
        dimension_classification.classification_id = "5A"
        dimension_classification.includes_parents = False
        dimension_classification.includes_all = False
        dimension_classification.includes_unknown = False
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        # So neither match the dimension_classification
        dimension_fixture = Dimension.query.one()
        assert dimension_fixture.classification_source_string == "Manually selected"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_and_no_table(
        self, db_session, stub_page_with_dimension_and_chart
    ):
        dimension_classification = DimensionClassification.query.one()
        # Ensure the classification matches that of the chart
        dimension_classification.classification_id = "2A"
        dimension_classification.includes_parents = False
        dimension_classification.includes_all = True
        dimension_classification.includes_unknown = False
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        dimension_fixture = Dimension.query.one()
        assert dimension_fixture.classification_source_string == "Chart"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_but_not_with_table(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_classification = DimensionClassification.query.one()
        # Ensure the classification matches that of the chart
        dimension_classification.classification_id = "2A"
        dimension_classification.includes_parents = False
        dimension_classification.includes_all = True
        dimension_classification.includes_unknown = False
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        dimension_fixture = Dimension.query.one()
        assert dimension_fixture.classification_source_string == "Chart"

    def test_classification_source_string_is_table_if_match_with_table_classification_but_not_with_chart(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_classification = DimensionClassification.query.one()
        # Ensure the classification matches that of the table
        dimension_classification.classification_id = "5A"
        dimension_classification.includes_parents = True
        dimension_classification.includes_all = False
        dimension_classification.includes_unknown = True
        db_session.session.add(dimension_classification)
        db_session.session.commit()

        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        dimension_fixture = Dimension.query.one()
        assert dimension_fixture.classification_source_string == "Table"

    def test_classification_source_string_is_table_if_match_with_both_table_and_chart_classification(
        self, db_session, stub_page_with_dimension_and_chart_and_table
    ):
        dimension_fixture = Dimension.query.one()
        dimension_classification = DimensionClassification.query.one()
        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        # Ensure the classification matches that of the chart
        dimension_classification.classification_id = "2A"
        dimension_classification.includes_parents = False
        dimension_classification.includes_all = True
        dimension_classification.includes_unknown = False

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

    def test_copy_dimension_also_copies_classification_links(self, db_session, stub_page_with_dimension_and_chart):
        # Given a dimension with a classification link
        dimension_fixture = Dimension.query.one()
        dimension_fixture_guid = dimension_fixture.guid

        # When we make a copy of the dimension and commit it to the DB
        copied_dimension = dimension_fixture.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension_fixture = Dimension.query.filter(Dimension.guid == dimension_fixture_guid).one()

        # Then the classification link is also copied
        assert (
            len(copied_dimension.classification_links.all()) == len(dimension_fixture.classification_links.all()) == 1
        )
        assert (
            copied_dimension.dimension_classification.dimension_guid
            != dimension_fixture.dimension_classification.dimension_guid
        )
        assert (
            copied_dimension.dimension_classification.classification_id
            == dimension_fixture.dimension_classification.classification_id
        )
        assert (
            copied_dimension.dimension_classification.includes_parents
            == dimension_fixture.dimension_classification.includes_parents
        )
        assert (
            copied_dimension.dimension_classification.includes_all
            == dimension_fixture.dimension_classification.includes_all
        )
        assert (
            copied_dimension.dimension_classification.includes_unknown
            == dimension_fixture.dimension_classification.includes_unknown
        )

    def test_update_dimension_classification_from_chart_only(self, stub_page_with_dimension_and_chart):
        dimension_fixture = Dimension.query.one()
        dimension_fixture.update_dimension_classification_from_chart_or_table()

        assert dimension_fixture.dimension_classification is not None
        # The dimension_chart fixture has id "2A", includes_parents=False, includes_all=True, includes_unknown=False
        assert dimension_fixture.dimension_classification.classification_id == "2A"
        assert dimension_fixture.dimension_classification.includes_parents is False
        assert dimension_fixture.dimension_classification.includes_all is True
        assert dimension_fixture.dimension_classification.includes_unknown is False

    def test_update_dimension_classification_from_table_only(self, stub_page_with_dimension_and_chart_and_table):
        dimension_fixture = Dimension.query.one()
        dimension_fixture.dimension_chart = None
        dimension_fixture.update_dimension_classification_from_chart_or_table()

        assert dimension_fixture.dimension_classification is not None
        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        assert dimension_fixture.dimension_classification.classification_id == "5A"
        assert dimension_fixture.dimension_classification.includes_parents is True
        assert dimension_fixture.dimension_classification.includes_all is False
        assert dimension_fixture.dimension_classification.includes_unknown is True

    def test_update_dimension_classification_from_chart_and_table(self, stub_page_with_dimension_and_chart_and_table):
        dimension_fixture = Dimension.query.one()
        dimension_fixture.update_dimension_classification_from_chart_or_table()

        assert dimension_fixture.dimension_classification is not None
        # The dimension_table fixture has 5 items but dimension_chart has only two, so table is more specific
        # The dimension_table fixture has id "5A", includes_parents=True, includes_all=False, includes_unknown=True
        assert dimension_fixture.dimension_classification.classification_id == "5A"
        assert dimension_fixture.dimension_classification.includes_parents is True
        assert dimension_fixture.dimension_classification.includes_all is False
        assert dimension_fixture.dimension_classification.includes_unknown is True

    def test_update_dimension_classification_with_no_chart_or_table_deletes(self, stub_page_with_dimension_and_chart):
        # Given a dimension with a dimension classification based on chart
        dimension_fixture = Dimension.query.one()
        dimension_fixture.update_dimension_classification_from_chart_or_table()
        assert dimension_fixture.dimension_classification is not None

        # When the chart is deleted (so there is no chart or table) and dimension classification updated
        dimension_fixture.dimension_chart = None
        dimension_fixture.update_dimension_classification_from_chart_or_table()

        # Then the dimension_classification is deleted
        assert dimension_fixture.dimension_classification is None

    def test_delete_chart_from_dimension(self, stub_page_with_dimension_and_chart):
        dimension = Dimension.query.first()
        assert dimension.chart is not None
        assert dimension.chart_source_data is not None
        assert dimension.chart_2_source_data is not None
        assert dimension.dimension_chart is not None
        assert dimension.dimension_classification is not None

        # When the chart is deleted
        dimension.delete_chart()

        # refresh the dimension from the database
        dimension = Dimension.query.get(dimension.guid)

        # Then the chart attributes should have been removed
        assert dimension.chart is None
        assert dimension.chart_source_data is None
        assert dimension.chart_2_source_data is None

        # And the associated chart object should have been removed
        assert dimension.dimension_chart is None

        # And the dimension itself should have no classification as there's no chart or table
        assert dimension.dimension_classification is None

    def test_delete_table_from_dimension(stub_measure_page, stub_page_with_dimension_and_chart_and_table):
        dimension = Dimension.query.first()
        assert dimension.table is not None
        assert dimension.table_source_data is not None
        assert dimension.table_2_source_data is not None
        assert dimension.dimension_table is not None
        assert dimension.dimension_classification is not None
        # Classification 5A is set from table
        assert dimension.dimension_classification.classification_id == "5A"

        # When the table is deleted
        dimension.delete_table()

        # refresh the dimension from the database
        dimension = Dimension.query.get(dimension.guid)

        # Then it should have removed all the table data
        assert dimension.table is None
        assert dimension.table_source_data is None
        assert dimension.table_2_source_data is None

        # And the associated table metadata
        assert dimension.dimension_table is None

        # # Classification is now 2A, set from the remaining chart
        assert dimension.dimension_classification.classification_id == "2A"

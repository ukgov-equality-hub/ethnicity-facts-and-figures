import re
from datetime import datetime, timedelta

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from application.cms.exceptions import RejectionImpossible
from application.cms.models import Dimension, UKCountry, Table, Chart, DimensionClassification, MeasureVersion
from tests.models import (
    MeasureFactory,
    MeasureVersionFactory,
    MeasureVersionWithDimensionFactory,
    ClassificationFactory,
    EthnicityFactory,
    DimensionFactory,
    TableFactory,
    ChartFactory,
    TopicFactory,
)
from flaky import flaky


class TestDimensionModel:
    @flaky(max_runs=10, min_passes=1)
    def test_create_valid_dimension(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory()
        data = {"title": "Test dimension"}

        url = url_for(
            "cms.create_dimension",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
        resp = test_app_client.post(url, data=data, follow_redirects=False)

        assert resp.status_code == 302, "Should be redirected to edit page for dimension"
        assert re.match(
            rf"http://localhost:5000/cms/{measure_version.measure.subtopic.topic.slug}/"
            rf"{measure_version.measure.subtopic.slug}/{measure_version.measure.slug}/"
            rf"{measure_version.version}/[^/]+/edit",
            resp.location,
        )

    @flaky(max_runs=10, min_passes=1)
    def test_create_dimension_without_specifying_title(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory()

        url = url_for(
            "cms.create_dimension",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )

        resp = test_app_client.post(url, follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        assert page.find("title").string == "Error: Create dimension"

    @flaky(max_runs=10, min_passes=1)
    def test_update_dimension_with_valid_data(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionWithDimensionFactory()

        data = {"title": "Test dimension"}

        url = url_for(
            "cms.edit_dimension",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=measure_version.dimensions[0].guid,
        )
        resp = test_app_client.post(url, data=data, follow_redirects=False)

        assert resp.status_code == 302, "Should be redirected to edit page for dimension"
        assert re.match(
            rf"http://localhost:5000/cms/{measure_version.measure.subtopic.topic.slug}/"
            rf"{measure_version.measure.subtopic.slug}/{measure_version.measure.slug}/"
            rf"{measure_version.version}/[^/]+/edit",
            resp.location,
        )

    @flaky(max_runs=10, min_passes=1)
    def test_update_dimension_with_invalid_data(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionWithDimensionFactory(title="Stop and search", dimensions__title="By ethnicity")

        data = {"title": ""}

        url = url_for(
            "cms.edit_dimension",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=measure_version.dimensions[0].guid,
        )
        resp = test_app_client.post(url, data=data, follow_redirects=False)
        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")

        assert resp.status_code == 400
        assert page.find("title").string == "Error: Edit dimension – Stop and search: By ethnicity"

    def test_classification_source_string_is_none_if_no_dimension_classification(self):
        measure_version = MeasureVersionWithDimensionFactory(dimensions__classification_links=[])
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string is None

    def test_classification_source_string_is_manually_selected_if_no_chart_or_table_classification(self):
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__dimension_chart__settings_and_source_data__classification=None,
            dimensions__dimension_table__settings_and_source_data__classification=None,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Manually selected"

    def test_classification_source_string_is_manually_selected_if_no_match_with_chart_or_table_classification(self):
        classification_2a = ClassificationFactory(id="2A")
        classification_5a = ClassificationFactory(id="5A")
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension table
            dimensions__dimension_table__classification=classification_5a,
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # The dimension classification defined here does not match the chart or table
            dimensions__classification_links__classification=classification_5a,
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Manually selected"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_and_no_table(self):
        classification_2a = ClassificationFactory(id="2A")
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # No table
            dimensions__dimension_table=None,
            # The dimension classification defined here is the same as for the chart
            dimensions__classification_links__classification=classification_2a,
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Chart"

    def test_classification_source_string_is_chart_if_match_with_chart_classification_but_not_with_table(self):
        classification_2a = ClassificationFactory(id="2A")
        classification_5a = ClassificationFactory(id="5A")
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension table
            dimensions__dimension_table__classification=classification_5a,
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # The dimension classification defined here is the same as for the chart but not as the table
            dimensions__classification_links__classification=classification_2a,
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Chart"

    def test_classification_source_string_is_table_if_match_with_table_classification_but_not_with_chart(self):
        classification_2a = ClassificationFactory(id="2A")
        classification_5a = ClassificationFactory(id="5A")
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension table
            dimensions__dimension_table__classification=classification_5a,
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # The dimension classification defined here is the same as for the table but not as the chart
            dimensions__classification_links__classification=classification_5a,
            dimensions__classification_links__includes_parents=True,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Table"

    def test_classification_source_string_is_table_if_match_with_both_table_and_chart_classification(self):
        classification_2a = ClassificationFactory(id="2A")
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension_chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension_table
            dimensions__dimension_table__classification=classification_2a,
            dimensions__dimension_table__includes_parents=False,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # The dimension classification defined here is the same as both the table and the chart
            dimensions__classification_links__classification=classification_2a,
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string == "Table"

    def test_copy_dimension_makes_copies_of_chart_and_table(self, db_session):
        measure_version = MeasureVersionWithDimensionFactory()
        dimension = measure_version.dimensions[0]
        dimension_guid = dimension.guid
        original_chart_id = dimension.chart_id
        original_table_id = dimension.table_id

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension = Dimension.query.filter(Dimension.guid == dimension_guid).one()

        # The copied dimension has a new Chart attached to it
        assert copied_dimension.dimension_chart is not None
        assert copied_dimension.chart_id != original_chart_id
        # The original dimension still has the old chart
        assert dimension.chart_id == original_chart_id
        # The copied Chart is the same as the original Chart
        assert copied_dimension.dimension_chart.classification_id == dimension.dimension_chart.classification_id
        assert copied_dimension.dimension_chart.includes_all == dimension.dimension_chart.includes_all
        assert copied_dimension.dimension_chart.includes_parents == dimension.dimension_chart.includes_parents
        assert copied_dimension.dimension_chart.includes_unknown == dimension.dimension_chart.includes_unknown

        # The copied dimension has a new Table attached to it
        assert copied_dimension.dimension_table is not None
        assert copied_dimension.table_id != original_table_id
        # The original dimension still has the old table
        assert dimension.table_id == original_table_id
        # The copied Table is the same as the original Table
        assert copied_dimension.dimension_table.classification_id == dimension.dimension_table.classification_id
        assert copied_dimension.dimension_table.includes_all == dimension.dimension_table.includes_all
        assert copied_dimension.dimension_table.includes_parents == dimension.dimension_table.includes_parents
        assert copied_dimension.dimension_table.includes_unknown == dimension.dimension_table.includes_unknown

    def test_copy_dimension_can_copy_dimensions_without_chart_or_table(self, db_session):
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__dimension_table=None, dimensions__dimension_chart=None
        )
        dimension = measure_version.dimensions[0]
        dimension_guid = dimension.guid
        original_chart_id = dimension.chart_id
        original_table_id = dimension.table_id

        # The dimension has no chart or table to start with
        assert original_chart_id is None
        assert original_table_id is None

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension = Dimension.query.filter(Dimension.guid == dimension_guid).one()

        # Both the original and copied dimensions have no Chart or Table
        assert dimension.dimension_chart is None
        assert copied_dimension.chart_id is None
        assert copied_dimension.dimension_chart is None

        assert dimension.dimension_table is None
        assert copied_dimension.table_id is None
        assert copied_dimension.dimension_table is None

    def test_copy_dimension_can_copy_dimensions_with_one_chart_or_table(self, db_session):
        measure_version = MeasureVersionWithDimensionFactory(dimensions__dimension_table=None)
        dimension = measure_version.dimensions[0]
        dimension_guid = dimension.guid
        original_chart_id = dimension.chart_id
        original_table_id = dimension.table_id

        # The dimension has no table to start with
        assert original_chart_id is not None
        assert original_table_id is None

        # Make a copy of a dimension and commit it to the DB
        copied_dimension = dimension.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension = Dimension.query.filter(Dimension.guid == dimension_guid).one()

        # The copied dimension has a new Chart attached to it
        assert copied_dimension.dimension_chart is not None
        assert copied_dimension.chart_id != original_chart_id
        # The original dimension still has the old chart
        assert dimension.chart_id == original_chart_id
        # The copied Chart is the same as the original Chart
        assert copied_dimension.dimension_chart.classification_id == dimension.dimension_chart.classification_id
        assert copied_dimension.dimension_chart.includes_all == dimension.dimension_chart.includes_all
        assert copied_dimension.dimension_chart.includes_parents == dimension.dimension_chart.includes_parents
        assert copied_dimension.dimension_chart.includes_unknown == dimension.dimension_chart.includes_unknown

        # Both the original and copied dimensions have no Table
        assert dimension.dimension_table is None
        assert copied_dimension.table_id is None
        assert copied_dimension.dimension_table is None

    def test_copy_dimension_also_copies_classification_links(self, db_session):
        # Given a dimension with a classification link
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__classification_links__classification__id="2A",
            dimensions__classification_links__includes_parents=False,
            dimensions__classification_links__includes_all=False,
            dimensions__classification_links__includes_unknown=True,
        )
        dimension = measure_version.dimensions[0]
        dimension_guid = dimension.guid

        # When we make a copy of the dimension and commit it to the DB
        copied_dimension = dimension.copy()
        db_session.session.add(copied_dimension)
        db_session.session.commit()

        # Re-fetch original dimension from db before asserting things about it
        dimension_fixture = Dimension.query.filter(Dimension.guid == dimension_guid).one()

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
            == "2A"
        )
        assert (
            copied_dimension.dimension_classification.includes_parents
            == dimension_fixture.dimension_classification.includes_parents
            == False
        )
        assert (
            copied_dimension.dimension_classification.includes_all
            == dimension_fixture.dimension_classification.includes_all
            == False
        )
        assert (
            copied_dimension.dimension_classification.includes_unknown
            == dimension_fixture.dimension_classification.includes_unknown
            == True
        )

    def test_update_dimension_classification_from_chart_only(self):
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=ClassificationFactory(id="2A"),
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # No table
            dimensions__dimension_table=None,
            # No dimension classification link
            dimensions__classification_links=[],
        )
        dimension = measure_version.dimensions[0]
        assert dimension.dimension_classification is None

        dimension.update_dimension_classification_from_chart_or_table()

        assert dimension.dimension_classification is not None
        assert dimension.dimension_classification.classification_id == "2A"
        assert dimension.dimension_classification.includes_parents is False
        assert dimension.dimension_classification.includes_all is False
        assert dimension.dimension_classification.includes_unknown is True

    def test_update_dimension_classification_from_table_only(self):
        measure_version = MeasureVersionWithDimensionFactory(
            # No chart
            dimensions__dimension_chart=None,
            # Dimension table
            dimensions__dimension_table__classification=ClassificationFactory(id="5A"),
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # No dimension classification link
            dimensions__classification_links=[],
        )
        dimension = measure_version.dimensions[0]
        assert dimension.dimension_classification is None

        dimension.update_dimension_classification_from_chart_or_table()

        assert dimension.dimension_classification is not None
        assert dimension.dimension_classification.classification_id == "5A"
        assert dimension.dimension_classification.includes_parents is True
        assert dimension.dimension_classification.includes_all is False
        assert dimension.dimension_classification.includes_unknown is True

    def test_update_dimension_classification_from_chart_and_table(self):
        classification_2a = ClassificationFactory(
            id="2A", ethnicities=[EthnicityFactory(value="one"), EthnicityFactory(value="two")]
        )
        classification_3a = ClassificationFactory(
            id="3A",
            ethnicities=[EthnicityFactory(value="one"), EthnicityFactory(value="two"), EthnicityFactory(value="three")],
        )
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension table
            dimensions__dimension_table__classification=classification_3a,
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            # No classification link
            dimensions__classification_links=[],
        )
        dimension = measure_version.dimensions[0]
        assert dimension.dimension_classification is None

        dimension.update_dimension_classification_from_chart_or_table()

        assert dimension.dimension_classification is not None
        # The classification_3a has 3 items but classification_2a has only two, so table is more specific
        assert dimension.dimension_classification.classification_id == "3A"
        assert dimension.dimension_classification.includes_parents is True
        assert dimension.dimension_classification.includes_all is False
        assert dimension.dimension_classification.includes_unknown is True

    def test_update_dimension_classification_with_no_chart_or_table_deletes(self):
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=ClassificationFactory(id="2A"),
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # No table
            dimensions__dimension_table=None,
            # No dimension classification link
            dimensions__classification_links=[],
        )
        # Given a dimension with a dimension classification based on chart
        dimension = measure_version.dimensions[0]
        assert dimension.dimension_classification is None
        dimension.update_dimension_classification_from_chart_or_table()
        assert dimension.dimension_classification is not None

        # When the chart is deleted (so there is no chart or table) and dimension classification updated
        dimension.dimension_chart = None
        dimension.update_dimension_classification_from_chart_or_table()

        # Then the dimension_classification is deleted
        assert dimension.dimension_classification is None

    def test_delete_chart_from_dimension(self):
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__dimension_chart__chart_object={"chart": "foobar"},
            dimensions__dimension_chart__settings_and_source_data={"xAxis": "time"},
            dimensions__dimension_table=None,
        )
        dimension = measure_version.dimensions[0]
        assert dimension.dimension_chart is not None
        assert dimension.dimension_chart.chart_object is not None
        assert dimension.dimension_chart.settings_and_source_data is not None
        assert dimension.dimension_classification is not None

        # When the chart is deleted
        dimension.dimension_chart.delete()

        # refresh the dimension from the database
        dimension = Dimension.query.get(dimension.guid)

        # And the associated chart object should have been removed
        assert dimension.dimension_chart is None

        # And the dimension itself should have no classification as there's no chart or table
        assert dimension.dimension_classification is None

    def test_delete_table_from_dimension(self):
        classification_2a = ClassificationFactory(
            id="2A", ethnicities=[EthnicityFactory(value="one"), EthnicityFactory(value="two")]
        )
        classification_3a = ClassificationFactory(
            id="3A",
            ethnicities=[EthnicityFactory(value="one"), EthnicityFactory(value="two"), EthnicityFactory(value="three")],
        )
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__classification=classification_2a,
            dimensions__dimension_chart__includes_parents=False,
            dimensions__dimension_chart__includes_all=False,
            dimensions__dimension_chart__includes_unknown=True,
            # Dimension table
            dimensions__dimension_table__classification=classification_3a,
            dimensions__dimension_table__includes_parents=True,
            dimensions__dimension_table__includes_all=False,
            dimensions__dimension_table__includes_unknown=True,
            dimensions__dimension_table__table_object={"col1": "ethnicity"},
            dimensions__dimension_table__settings_and_source_data={"foo": "bar"},
        )
        dimension = measure_version.dimensions[0]

        assert dimension.dimension_table is not None
        assert dimension.dimension_table.table_object is not None
        assert dimension.dimension_table.settings_and_source_data is not None
        assert dimension.dimension_classification is not None
        # Classification 3A is set from the table
        dimension.update_dimension_classification_from_chart_or_table()
        assert dimension.dimension_classification.classification_id == "3A"

        # When the table is deleted
        dimension.dimension_table.delete()

        # refresh the dimension from the database
        dimension = Dimension.query.get(dimension.guid)

        # Then it should have removed all the table data
        assert dimension.dimension_table is None

        # Classification is now 2A, set from the remaining chart
        assert dimension.dimension_classification.classification_id == "2A"

    def test_delete_dimension_removes_dimension_chart_table_and_classification(self, db_session):
        measure_version = MeasureVersionWithDimensionFactory(
            # Dimension chart
            dimensions__dimension_chart__chart_object={"chart": "yes"},
            dimensions__dimension_chart__settings_and_source_data={"source": "settings"},
            # Dimension table
            dimensions__dimension_table__table_object={"table": "yes"},
            dimensions__dimension_table__settings_and_source_data={"source": "data"},
        )
        dimension = measure_version.dimensions[0]

        dimension_table_id = dimension.table_id
        dimension_chart_id = dimension.chart_id
        dimension_guid = dimension.guid
        dimension_classification_links = list(dimension.classification_links)

        # Given the dimension has associated chart, table and classification entries
        assert Chart.query.get(dimension_chart_id) is not None
        assert Table.query.get(dimension_table_id) is not None
        assert len(dimension_classification_links) == 1
        assert (
            DimensionClassification.query.filter_by(dimension_guid=dimension_guid).all()
            == dimension_classification_links
        )

        # When the dimension is deleted
        db_session.session.delete(dimension)
        db_session.session.flush()

        # Then the associated chart, table and classification entries are deleted too
        assert Table.query.get(dimension_table_id) is None
        assert Chart.query.get(dimension_chart_id) is None
        assert DimensionClassification.query.filter_by(dimension_guid=dimension_guid).all() == []

    def test_to_dict(self):
        dimension = DimensionFactory.build(
            guid="dimension-guid",
            title="My dimension",
            time_period="2010/11",
            summary="My dimension summary",
            position=1,
        )
        MeasureVersionFactory(id=123, measure__id=456, dimensions=[dimension])

        assert dimension.to_dict() == {
            "guid": "dimension-guid",
            "title": "My dimension",
            "time_period": "2010/11",
            "summary": "My dimension summary",
            "position": 1,
            "measure_id": 456,
            "measure_version_id": 123,
            "dimension_chart": dimension.dimension_chart.to_dict(),
            "dimension_table": dimension.dimension_table.to_dict(),
            "static_file_name": "my-dimension.csv",
            "static_table_file_name": "my-dimension-table.csv",
        }

    def test_file_names(self):
        dimension = DimensionFactory.build(
            guid="dimension-guid",
            title="My dimension",
            time_period="2010/11",
            summary="My dimension summary",
            position=1,
        )

        assert dimension.static_file_name == "my-dimension.csv"
        assert dimension.static_table_file_name == "my-dimension-table.csv"

        dimension.title = None
        assert dimension.static_file_name == "dimension-guid.csv"
        assert dimension.static_table_file_name == "dimension-guid-table.csv"


class TestMeasureModel:
    def test_versions_to_publish(self):

        measure = MeasureFactory.create()
        measure_version_1_0 = MeasureVersionFactory.build(
            measure=measure, version="1.0", status="APPROVED", published_at=datetime(2018, 1, 19).date()
        )
        measure_version_1_1 = MeasureVersionFactory.build(
            measure=measure, version="1.1", status="APPROVED", published_at=datetime(2018, 1, 20).date()
        )
        measure_version_1_2 = MeasureVersionFactory.build(
            measure=measure, version="1.2", status="APPROVED", published_at=datetime(2018, 1, 21).date()
        )
        measure_version_2_0 = MeasureVersionFactory.build(
            measure=measure, version="2.0", status="APPROVED", published_at=datetime(2019, 1, 19).date()
        )
        MeasureVersionFactory.build(measure=measure, version="2.1", status="DRAFT", published_at=None)

        assert len(measure.versions_to_publish) == 4
        assert measure.versions_to_publish == [
            measure_version_2_0,
            measure_version_1_2,
            measure_version_1_1,
            measure_version_1_0,
        ]


class TestMeasureVersionModel:
    def test_publish_to_internal_review(self):
        measure_version = MeasureVersionFactory(status="DRAFT")
        measure_version.next_state()
        assert measure_version.status == "INTERNAL_REVIEW"

    def test_publish_to_department_review(self):
        measure_version = MeasureVersionFactory(status="INTERNAL_REVIEW")
        measure_version.next_state()
        assert measure_version.status == "DEPARTMENT_REVIEW"

    def test_publish_to_approved(self):
        measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
        measure_version.next_state()
        assert measure_version.status == "APPROVED"

    def test_reject_in_internal_review(self):
        measure_version = MeasureVersionFactory(status="INTERNAL_REVIEW")
        measure_version.reject()
        assert measure_version.status == "REJECTED"

    def test_reject_in_department_review(self):
        measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
        measure_version.reject()
        assert measure_version.status == "REJECTED"

    def test_cannot_reject_approved_page(self):
        measure_version = MeasureVersionFactory(status="APPROVED")
        with pytest.raises(RejectionImpossible):
            measure_version.reject()

    @pytest.mark.parametrize(
        "status, should_be_eligible",
        [
            ("DRAFT", False),
            ("INTERNAL_REVIEW", False),
            ("DEPARTMENT_REVIEW", False),
            ("REJECTED", False),
            ("APPROVED", True),
        ],
    )
    def test_page_should_be_eligible_for_build_only_in_right_state(self, status, should_be_eligible):

        measure_version = MeasureVersionFactory(status=status)
        assert measure_version.eligible_for_build() is should_be_eligible

    def test_available_actions_for_page_in_draft(self):
        measure_version = MeasureVersionFactory(status="DRAFT")
        expected_available_actions = ["APPROVE", "UPDATE"]

        assert expected_available_actions == measure_version.available_actions

    def test_available_actions_for_page_in_internal_review(self):
        measure_version = MeasureVersionFactory(status="INTERNAL_REVIEW")
        expected_available_actions = ["APPROVE", "REJECT"]

        assert expected_available_actions == measure_version.available_actions

    def test_available_actions_for_page_in_department_review(self):
        measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
        expected_available_actions = ["APPROVE", "REJECT"]

        assert expected_available_actions == measure_version.available_actions

    def test_available_actions_for_rejected_page(self):
        measure_version = MeasureVersionFactory(status="REJECTED")
        expected_available_actions = ["RETURN_TO_DRAFT"]

        assert expected_available_actions == measure_version.available_actions

    def test_available_actions_for_approved_page(self):
        measure_version = MeasureVersionFactory(status="APPROVED")
        expected_available_actions = []

        assert expected_available_actions == measure_version.available_actions

    def test_page_sort_by_version(self):

        measure = MeasureFactory()
        first_version = MeasureVersionFactory(measure=measure, version="1.0")
        second_version = MeasureVersionFactory(measure=measure, version="1.1")
        third_version = MeasureVersionFactory(measure=measure, version="2.0")
        fourth_version = MeasureVersionFactory(measure=measure, version="2.2")
        fifth_version = MeasureVersionFactory(measure=measure, version="2.10")
        sixth_version = MeasureVersionFactory(measure=measure, version="2.20")

        versions = [fourth_version, sixth_version, fifth_version, second_version, first_version, third_version]

        versions.sort()

        assert versions[0] == first_version
        assert versions[1] == second_version
        assert versions[2] == third_version
        assert versions[3] == fourth_version
        assert versions[4] == fifth_version
        assert versions[5] == sixth_version

    def test_page_has_minor_update(self):
        measure = MeasureFactory()
        major_version = MeasureVersionFactory(version="1.0", measure=measure)
        MeasureVersionFactory(version="1.1", measure=measure)

        major_version.has_minor_update()

    def test_page_has_later_published_versions(self):
        measure = MeasureFactory()
        major_version_1 = MeasureVersionFactory(version="1.0", status="APPROVED", measure=measure)
        minor_version_2 = MeasureVersionFactory(version="1.1", status="APPROVED", measure=measure)
        minor_version_3 = MeasureVersionFactory(version="1.2", status="APPROVED", measure=measure)
        minor_version_4 = MeasureVersionFactory(version="1.3", status="DRAFT", measure=measure)

        assert major_version_1.has_no_later_published_versions() is False
        assert minor_version_2.has_no_later_published_versions() is False
        assert minor_version_3.has_no_later_published_versions() is True
        assert minor_version_4.has_no_later_published_versions() is True

    def test_is_minor_or_minor_version(self):
        measure_version = MeasureVersionFactory(version="1.0")

        assert measure_version.version == "1.0"
        assert measure_version.is_major_version() is True
        assert measure_version.is_minor_version() is False

        measure_version.version = measure_version.next_minor_version()

        assert measure_version.version == "1.1"
        assert measure_version.is_major_version() is False
        assert measure_version.is_minor_version() is True

        measure_version.version = measure_version.next_major_version()

        assert measure_version.version == "2.0"
        assert measure_version.is_major_version() is True
        assert measure_version.is_minor_version() is False

    @pytest.mark.parametrize(
        "page_versions, expected_order",
        (
            (["1.0", "1.1", "1.2", "2.0"], ["2.0", "1.2", "1.1", "1.0"]),
            (["2.0", "1.2", "1.1", "1.0"], ["2.0", "1.2", "1.1", "1.0"]),
            (["2.0", "4.1", "3.0", "8.2", "1.0"], ["8.2", "4.1", "3.0", "2.0", "1.0"]),
        ),
    )
    def test_measure_versions_returns_pages_ordered_by_version(self, page_versions, expected_order):
        measure = MeasureFactory()
        for version in page_versions:
            MeasureVersionFactory(measure=measure, version=version)

        assert [mv.version for mv in measure.versions] == expected_order

    def test_measure_latest_version_returns_latest_measure_version(self):
        measure = MeasureFactory()
        MeasureVersionFactory(version="1.0", latest=False, measure=measure)
        MeasureVersionFactory(version="3.1", latest=True, measure=measure)
        MeasureVersionFactory(version="2.0", latest=False, measure=measure)
        MeasureVersionFactory(version="3.0", latest=False, measure=measure)

        assert measure.latest_version.version == "3.1"

    def test_measure_latest_published_version_returns_latest_published_version(self):
        measure = MeasureFactory()
        MeasureVersionFactory(version="1.0", latest=False, status="APPROVED", measure=measure)
        MeasureVersionFactory(version="2.0", latest=False, status="APPROVED", measure=measure)
        MeasureVersionFactory(version="3.0", latest=False, status="APPROVED", measure=measure)
        MeasureVersionFactory(version="3.1", latest=True, status="DEPARTMENT_REVIEW", measure=measure)

        assert measure.latest_published_version.version == "3.0"

    @pytest.mark.parametrize(
        "countries, formatted_string",
        (
            ([UKCountry.ENGLAND], "England"),
            ([UKCountry.ENGLAND, UKCountry.WALES], "England and Wales"),
            ([UKCountry.ENGLAND, UKCountry.WALES, UKCountry.SCOTLAND, UKCountry.NORTHERN_IRELAND], "United Kingdom"),
            ([UKCountry.OVERSEAS], "Overseas"),
            ([UKCountry.OVERSEAS, UKCountry.ENGLAND], "Overseas and England"),
            ([UKCountry.ENGLAND, UKCountry.OVERSEAS], "England and overseas"),
            ([UKCountry.ENGLAND, UKCountry.SCOTLAND, UKCountry.OVERSEAS], "England, Scotland and overseas"),
            (
                [
                    UKCountry.ENGLAND,
                    UKCountry.WALES,
                    UKCountry.SCOTLAND,
                    UKCountry.NORTHERN_IRELAND,
                    UKCountry.OVERSEAS,
                ],
                "UK and overseas",
            ),
        ),
    )
    def test_area_covered_formatter(self, countries, formatted_string):
        measure_version = MeasureVersionFactory(area_covered=countries)

        assert measure_version.format_area_covered() == formatted_string

    def test_first_published_date(self):
        v1_publication_date = datetime(2018, 1, 19).date()
        v2_publication_date = datetime(2018, 2, 19).date()
        measure = MeasureFactory()
        major_version_1 = MeasureVersionFactory(
            version="1.0", status="APPROVED", measure=measure, published_at=v1_publication_date
        )
        major_version_2 = MeasureVersionFactory(
            version="2.0", status="APPROVED", measure=measure, published_at=v2_publication_date
        )
        minor_version_2_1 = MeasureVersionFactory(
            version="2.1", status="APPROVED", measure=measure, published_at=v2_publication_date + timedelta(days=30)
        )
        minor_version_2_2 = MeasureVersionFactory(
            version="2.2", status="APPROVED", measure=measure, published_at=v2_publication_date + timedelta(days=60)
        )

        assert major_version_1.first_published_date == v1_publication_date
        assert major_version_2.first_published_date == v2_publication_date
        assert minor_version_2_1.first_published_date == v2_publication_date
        assert minor_version_2_2.first_published_date == v2_publication_date

    def test_get_previous_version(self):
        measure = MeasureFactory()
        mv1_0 = MeasureVersionFactory(version="1.0", measure=measure)
        mv1_1 = MeasureVersionFactory(version="1.1", measure=measure)
        mv1_2 = MeasureVersionFactory(version="1.2", measure=measure)
        mv2_0 = MeasureVersionFactory(version="2.0", measure=measure)
        mv2_1 = MeasureVersionFactory(version="2.1", measure=measure)
        mv3_0 = MeasureVersionFactory(version="3.0", measure=measure)

        assert mv1_0.get_previous_version() is None
        assert mv1_1.get_previous_version() is mv1_0
        assert mv1_2.get_previous_version() is mv1_1
        assert mv2_0.get_previous_version() is mv1_2
        assert mv2_1.get_previous_version() is mv2_0
        assert mv3_0.get_previous_version() is mv2_1

    def test_social_description_uses_description_when_present(self):
        measure_version = MeasureVersionFactory(description="Test description")

        assert measure_version.social_description == "Test description"

    def test_social_description_uses_first_bullet_when_no_description_present(self):
        measure_version = MeasureVersionFactory(
            description=None, summary="* This is the first main point\n\n* This is the second main point"
        )

        assert measure_version.social_description == "* This is the first main point"

    def test_social_description_returns_nil_if_no_description_or_bullets_present(self):
        measure_version = MeasureVersionFactory(description=None, summary=None)

        assert measure_version.social_description is None

    def test_social_description_returns_nil_if_no_description_or_summary_doesnt_have_bullets(self):
        measure_version = MeasureVersionFactory(description=None, summary="This is an intro.")

        assert measure_version.social_description is None

    def test_previous_minor_versions(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.0")
        mv_1_1: MeasureVersion = MeasureVersionFactory.build(status="APPROVED", version="1.1", measure=mv_1_0.measure)
        mv_1_2: MeasureVersion = MeasureVersionFactory.build(status="APPROVED", version="1.2", measure=mv_1_0.measure)
        mv_1_3: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="1.3", measure=mv_1_0.measure)
        mv_2_0: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="2.0", measure=mv_1_0.measure)

        db_session.session.commit()

        assert mv_1_0.previous_minor_versions == []
        assert mv_1_1.previous_minor_versions == [mv_1_0]
        assert mv_1_2.previous_minor_versions == [mv_1_1, mv_1_0]
        assert mv_1_3.previous_minor_versions == [mv_1_2, mv_1_1, mv_1_0]
        assert mv_2_0.previous_minor_versions == []

    def test_previous_published_minor_versions(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.0")
        mv_1_1: MeasureVersion = MeasureVersionFactory.build(status="APPROVED", version="1.1", measure=mv_1_0.measure)
        mv_1_2: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="1.2", measure=mv_1_0.measure)
        mv_1_3: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="1.3", measure=mv_1_0.measure)
        mv_2_0: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="2.0", measure=mv_1_0.measure)

        db_session.session.commit()

        assert mv_1_0.previous_published_minor_versions == []
        assert mv_1_1.previous_published_minor_versions == [mv_1_0]
        assert mv_1_2.previous_published_minor_versions == [mv_1_1, mv_1_0]
        assert mv_1_3.previous_published_minor_versions == [mv_1_1, mv_1_0]
        assert mv_2_0.previous_published_minor_versions == []

    def test_later_minor_versions(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.0")
        mv_1_1: MeasureVersion = MeasureVersionFactory.build(status="APPROVED", version="1.1", measure=mv_1_0.measure)
        mv_1_2: MeasureVersion = MeasureVersionFactory.build(status="APPROVED", version="1.2", measure=mv_1_0.measure)
        mv_1_3: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="1.3", measure=mv_1_0.measure)
        mv_2_0: MeasureVersion = MeasureVersionFactory.build(status="DRAFT", version="2.0", measure=mv_1_0.measure)

        db_session.session.commit()

        assert mv_1_0.later_minor_versions == [mv_1_3, mv_1_2, mv_1_1]
        assert mv_1_1.later_minor_versions == [mv_1_3, mv_1_2]
        assert mv_1_2.later_minor_versions == [mv_1_3]
        assert mv_1_3.later_minor_versions == []
        assert mv_2_0.later_minor_versions == []

    def test_latest_published_minor_version(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.0")
        mv_1_1: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.1", measure=mv_1_0.measure)
        mv_1_2: MeasureVersion = MeasureVersionFactory.create(status="APPROVED", version="1.2", measure=mv_1_0.measure)
        mv_1_3: MeasureVersion = MeasureVersionFactory.create(status="DRAFT", version="1.3", measure=mv_1_0.measure)
        mv_2_0: MeasureVersion = MeasureVersionFactory.create(status="DRAFT", version="2.0", measure=mv_1_0.measure)

        db_session.session.commit()

        assert mv_1_0.latest_published_minor_version == mv_1_2
        assert mv_1_1.latest_published_minor_version == mv_1_2
        assert mv_1_2.latest_published_minor_version == mv_1_2
        assert mv_1_3.latest_published_minor_version == mv_1_2
        assert mv_2_0.latest_published_minor_version is None

    def test_has_known_statistical_errors(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(
            version="1.0", update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_1_1: MeasureVersion = MeasureVersionFactory.create(
            version="1.1", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_1_2: MeasureVersion = MeasureVersionFactory.create(
            version="1.2",
            measure=mv_1_0.measure,
            update_corrects_data_mistake=True,
            update_corrects_measure_version=mv_1_1.id,
            status="APPROVED",
        )
        mv_1_3: MeasureVersion = MeasureVersionFactory.create(
            version="1.3", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_1_4: MeasureVersion = MeasureVersionFactory.create(
            version="1.4",
            measure=mv_1_0.measure,
            update_corrects_data_mistake=True,
            update_corrects_measure_version=mv_1_3.id,
            status="APPROVED",
        )
        mv_1_5: MeasureVersion = MeasureVersionFactory.create(
            version="1.5", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )

        mv_2_0: MeasureVersion = MeasureVersionFactory.build(
            version="2.0", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )

        mv_2_1: MeasureVersion = MeasureVersionFactory.build(
            version="2.1",
            measure=mv_1_0.measure,
            update_corrects_data_mistake=True,
            status="DRAFT",
            update_corrects_measure_version=mv_2_0.id,
        )

        db_session.session.commit()

        assert mv_1_0.has_known_statistical_errors is False
        assert mv_1_1.has_known_statistical_errors is True
        assert mv_1_2.has_known_statistical_errors is False
        assert mv_1_3.has_known_statistical_errors is True
        assert mv_1_4.has_known_statistical_errors is False
        assert mv_1_5.has_known_statistical_errors is False
        assert mv_2_0.has_known_statistical_errors is False
        assert mv_2_1.has_known_statistical_errors is False

    def test_has_known_statistical_corrections(self, db_session):
        mv_1_0: MeasureVersion = MeasureVersionFactory.create(
            version="1.0", update_corrects_data_mistake=False, status="APPROVED"
        )

        mv_1_1: MeasureVersion = MeasureVersionFactory.create(
            version="1.1", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_1_2: MeasureVersion = MeasureVersionFactory.create(
            version="1.2",
            measure=mv_1_0.measure,
            update_corrects_data_mistake=True,
            update_corrects_measure_version=mv_1_1.id,
            status="APPROVED",
        )
        mv_1_3: MeasureVersion = MeasureVersionFactory.create(
            version="1.3", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_1_4: MeasureVersion = MeasureVersionFactory.create(
            version="1.4",
            measure=mv_1_0.measure,
            update_corrects_data_mistake=True,
            update_corrects_measure_version=mv_1_3.id,
            status="APPROVED",
        )
        mv_1_5: MeasureVersion = MeasureVersionFactory.create(
            version="1.5", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_2_0: MeasureVersion = MeasureVersionFactory.build(
            version="2.0", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="APPROVED"
        )
        mv_2_1: MeasureVersion = MeasureVersionFactory.build(
            version="2.1", measure=mv_1_0.measure, update_corrects_data_mistake=True, status="DRAFT"
        )
        mv_2_2: MeasureVersion = MeasureVersionFactory.build(
            version="2.2", measure=mv_1_0.measure, update_corrects_data_mistake=False, status="DRAFT"
        )

        db_session.session.commit()

        assert mv_1_0.has_known_statistical_corrections is False
        assert mv_1_1.has_known_statistical_corrections is False
        assert mv_1_2.has_known_statistical_corrections is True
        assert mv_1_3.has_known_statistical_corrections is True
        assert mv_1_4.has_known_statistical_corrections is True
        assert mv_1_5.has_known_statistical_corrections is True
        assert mv_2_0.has_known_statistical_corrections is False
        assert mv_2_1.has_known_statistical_corrections is True
        assert mv_2_2.has_known_statistical_corrections is False


class TestChartModel:
    def test_to_dict(self):
        chart = ChartFactory.build(
            includes_parents=False,
            includes_all=True,
            includes_unknown=True,
            settings_and_source_data={},
            chart_object={"chart": "object"},
        )

        assert chart.to_dict() == {
            "classification_id": chart.classification.id,
            "includes_parents": False,
            "includes_all": True,
            "includes_unknown": True,
            "settings_and_source_data": {},
            "chart_object": {"chart": "object"},
        }


class TestTableModel:
    def test_to_dict(self):
        table = TableFactory.build(
            includes_parents=False,
            includes_all=True,
            includes_unknown=True,
            settings_and_source_data={},
            table_object={"table": "object"},
        )

        assert table.to_dict() == {
            "classification_id": table.classification.id,
            "includes_parents": False,
            "includes_all": True,
            "includes_unknown": True,
            "settings_and_source_data": {},
            "table_object": {"table": "object"},
        }


class TestTopicModel:
    def test_topic_with_short_title(self):
        topic = TopicFactory.build(title="Long title", short_title="Short title")
        assert topic.short_title_or_title == "Short title"

    def test_topic_with_no_short_title(self):
        topic = TopicFactory.build(title="Long title", short_title=None)
        assert topic.short_title_or_title == "Long title"

import re
from datetime import datetime, timedelta

import pytest
from bs4 import BeautifulSoup
from flask import url_for

from application.cms.exceptions import RejectionImpossible
from application.cms.models import Dimension, UKCountry
from tests.models import (
    MeasureFactory,
    MeasureVersionFactory,
    MeasureVersionWithDimensionFactory,
    ClassificationFactory,
    EthnicityFactory,
)


class TestDimensionModel:
    def test_create_valid_dimension(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionFactory(
            version="1.0",
            measure__slug="measure",
            measure__subtopics__slug="subtopic",
            measure__subtopics__topic__slug="topic",
        )
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
        assert re.match(r"http://localhost:5000/cms/topic/subtopic/measure/1.0/[^/]+/edit", resp.location)

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

    def test_update_dimension_with_valid_data(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionWithDimensionFactory(
            version="1.0",
            measure__slug="measure",
            measure__subtopics__slug="subtopic",
            measure__subtopics__topic__slug="topic",
            dimensions__guid="dimension-guid",
        )

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
        assert re.match(r"http://localhost:5000/cms/topic/subtopic/measure/1.0/dimension-guid/edit", resp.location)

    def test_update_dimension_with_invalid_data(self, test_app_client, logged_in_rdu_user):

        measure_version = MeasureVersionWithDimensionFactory(
            version="1.0",
            measure__slug="measure",
            measure__subtopics__slug="subtopic",
            measure__subtopics__topic__slug="topic",
            dimensions__guid="dimension-guid",
        )

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
        assert page.find("title").string == "Error: Edit dimension"

    def test_classification_source_string_is_none_if_no_dimension_classification(self):
        measure_version = MeasureVersionWithDimensionFactory(dimensions__classification_links=[])
        dimension = measure_version.dimensions[0]

        assert dimension.classification_source_string is None

    def test_classification_source_string_is_manually_selected_if_no_chart_or_table_classification(self):
        measure_version = MeasureVersionWithDimensionFactory(
            dimensions__chart__clasification=None, dimensions__table__clasification=None
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
            dimensions__classification_links__classification=ClassificationFactory(id="2A"),
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
            dimensions__chart={"chart": "foobar"},
            dimensions__chart_source_data={"xAxis": "time"},
            dimensions__chart_2_source_data={"yAxis": "space"},
            dimensions__dimension_table=None,
        )
        dimension = measure_version.dimensions[0]
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
            dimensions__table={"col1": "ethnicity"},
            dimensions__table_source_data={"foo": "bar"},
            dimensions__table_2_source_data={"hey": "you"},
        )
        dimension = measure_version.dimensions[0]

        assert dimension.table is not None
        assert dimension.table_source_data is not None
        assert dimension.table_2_source_data is not None
        assert dimension.dimension_table is not None
        assert dimension.dimension_classification is not None
        # Classification 3A is set from the table
        dimension.update_dimension_classification_from_chart_or_table()
        assert dimension.dimension_classification.classification_id == "3A"

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

        # Classification is now 2A, set from the remaining chart
        assert dimension.dimension_classification.classification_id == "2A"


class TestMeasureVersion:
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

    def test_unpublish_page(self):
        measure_version = MeasureVersionFactory(status="APPROVED")
        measure_version.unpublish()
        assert measure_version.status == "UNPUBLISH"

    @pytest.mark.parametrize(
        "status, should_be_eligible",
        [
            ("DRAFT", False),
            ("INTERNAL_REVIEW", False),
            ("DEPARTMENT_REVIEW", False),
            ("REJECTED", False),
            ("UNPUBLISH", False),
            ("UNPUBLISHED", False),
            ("APPROVED", True),
        ],
    )
    def test_page_should_be_eligible_for_build_only_in_right_state(self, status, should_be_eligible):

        measure_version = MeasureVersionFactory(status=status)
        assert measure_version.eligible_for_build() is should_be_eligible

    def test_available_actions_for_page_in_draft(self):
        measure_version = MeasureVersionFactory(status="DRAFT")
        expected_available_actions = ["APPROVE", "UPDATE"]

        assert expected_available_actions == measure_version.available_actions()

    def test_available_actions_for_page_in_internal_review(self):
        measure_version = MeasureVersionFactory(status="INTERNAL_REVIEW")
        expected_available_actions = ["APPROVE", "REJECT"]

        assert expected_available_actions == measure_version.available_actions()

    def test_available_actions_for_page_in_department_review(self):
        measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
        expected_available_actions = ["APPROVE", "REJECT"]

        assert expected_available_actions == measure_version.available_actions()

    def test_available_actions_for_rejected_page(self):
        measure_version = MeasureVersionFactory(status="REJECTED")
        expected_available_actions = ["RETURN_TO_DRAFT"]

        assert expected_available_actions == measure_version.available_actions()

    def test_available_actions_for_approved_page(self):
        measure_version = MeasureVersionFactory(status="APPROVED")
        expected_available_actions = ["UNPUBLISH"]

        assert expected_available_actions == measure_version.available_actions()

    def test_no_available_actions_for_page_awaiting_unpublication(self):
        measure_version = MeasureVersionFactory(status="UNPUBLISH")
        expected_available_actions = []

        assert expected_available_actions == measure_version.available_actions()

    def test_available_actions_for_unpublished(self):
        measure_version = MeasureVersionFactory(status="UNPUBLISHED")
        expected_available_actions = ["RETURN_TO_DRAFT"]

        assert expected_available_actions == measure_version.available_actions()

    def test_page_sort_by_version(self):

        first_page = MeasureVersionFactory(guid="test_page", version="1.0")
        second_page = MeasureVersionFactory(guid="test_page", version="1.1")
        third_page = MeasureVersionFactory(guid="test_page", version="2.0")
        fourth_page = MeasureVersionFactory(guid="test_page", version="2.2")
        fifth_page = MeasureVersionFactory(guid="test_page", version="2.10")
        sixth_page = MeasureVersionFactory(guid="test_page", version="2.20")

        pages = [fourth_page, sixth_page, fifth_page, second_page, first_page, third_page]

        pages.sort()

        assert pages[0] == first_page
        assert pages[1] == second_page
        assert pages[2] == third_page
        assert pages[3] == fourth_page
        assert pages[4] == fifth_page
        assert pages[5] == sixth_page

    def test_page_has_minor_update(self):
        measure = MeasureFactory()
        major_version = MeasureVersionFactory(version="1.0", measure=measure)
        MeasureVersionFactory(version="1.1", measure=measure)

        major_version.has_minor_update()

    def test_page_has_later_published_versions(self):
        measure = MeasureFactory()
        major_version_1 = MeasureVersionFactory(version="1.0", published=True, status="APPROVED", measure=measure)
        minor_version_2 = MeasureVersionFactory(version="1.1", published=True, status="APPROVED", measure=measure)
        minor_version_3 = MeasureVersionFactory(version="1.2", published=True, status="APPROVED", measure=measure)
        minor_version_4 = MeasureVersionFactory(version="1.3", published=False, status="DRAFT", measure=measure)

        assert major_version_1.has_no_later_published_versions() is False
        assert minor_version_2.has_no_later_published_versions() is False
        assert minor_version_3.has_no_later_published_versions() is True
        assert minor_version_4.has_no_later_published_versions() is True

    def test_is_minor_or_minor_version(self):
        page = MeasureVersionFactory(guid="test_page", version="1.0")

        assert page.version == "1.0"
        assert page.is_major_version() is True
        assert page.is_minor_version() is False

        page.version = page.next_minor_version()

        assert page.version == "1.1"
        assert page.is_major_version() is False
        assert page.is_minor_version() is True

        page.version = page.next_major_version()

        assert page.version == "2.0"
        assert page.is_major_version() is True
        assert page.is_minor_version() is False

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
        MeasureVersionFactory(version="1.0", guid=measure.id, latest=False, measure=measure)
        MeasureVersionFactory(version="3.1", guid=measure.id, latest=True, measure=measure)
        MeasureVersionFactory(version="2.0", guid=measure.id, latest=False, measure=measure)
        MeasureVersionFactory(version="3.0", guid=measure.id, latest=False, measure=measure)

        assert measure.latest_version.version == "3.1"

    def test_measure_latest_published_version_returns_latest_published_version(self):
        measure = MeasureFactory()
        MeasureVersionFactory(version="1.0", guid=measure.id, latest=False, published=True, measure=measure)
        MeasureVersionFactory(version="2.0", guid=measure.id, latest=False, published=True, measure=measure)
        MeasureVersionFactory(version="3.0", guid=measure.id, latest=False, published=True, measure=measure)
        MeasureVersionFactory(version="3.1", guid=measure.id, latest=True, published=False, measure=measure)

        assert measure.latest_published_version.version == "3.0"

    @pytest.mark.parametrize(
        "page_versions, page_titles, expected_version_order, expected_title_order",
        (
            (["1.0", "2.0"], ["Test", "Test"], ["2.0", "1.0"], ["Test", "Test"]),
            (["2.0", "1.0"], ["Test", "Test"], ["2.0", "1.0"], ["Test", "Test"]),
            (["1.0", "2.0"], ["Test 1", "Test 2"], ["1.0", "2.0"], ["Test 1", "Test 2"]),
            (["2.0", "1.0"], ["Test 1", "Test 2"], ["2.0", "1.0"], ["Test 1", "Test 2"]),
            (
                ["2.0", "1.0", "3.0", "1.1"],
                ["Test", "Test", "Test", "Test"],
                ["3.0", "2.0", "1.1", "1.0"],
                ["Test", "Test", "Test", "Test"],
            ),
            (
                ["2.0", "1.0", "3.0", "1.1"],
                ["Test 1", "Test 3", "Test 2", "Test 2"],
                ["2.0", "3.0", "1.1", "1.0"],
                ["Test 1", "Test 2", "Test 2", "Test 3"],
            ),
        ),
    )
    def test_get_pages_by_type_returns_pages_ordered_by_title_and_version(
        self, page_service, page_versions, page_titles, expected_version_order, expected_title_order
    ):
        measure = MeasureFactory()
        for version, title in zip(page_versions, page_titles):
            MeasureVersionFactory(measure=measure, version=version, title=title, page_type="measure")

        pages = page_service.get_pages_by_type("measure")

        assert [page.title for page in pages] == expected_title_order
        assert [page.version for page in pages] == expected_version_order

    @pytest.mark.parametrize(
        "countries, formatted_string",
        (
            ([UKCountry.ENGLAND], "England"),
            ([UKCountry.ENGLAND, UKCountry.WALES], "England and Wales"),
            ([UKCountry.ENGLAND, UKCountry.WALES, UKCountry.SCOTLAND, UKCountry.NORTHERN_IRELAND], "United Kingdom"),
        ),
    )
    def test_area_covered_formatter(self, countries, formatted_string):
        measure_version = MeasureVersionFactory(guid="test_page", version="1.0", area_covered=countries)

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
        mv1_0 = MeasureVersionFactory(guid="guid", version="1.0", measure=measure)
        mv1_1 = MeasureVersionFactory(guid="guid", version="1.1", measure=measure)
        mv1_2 = MeasureVersionFactory(guid="guid", version="1.2", measure=measure)
        mv2_0 = MeasureVersionFactory(guid="guid", version="2.0", measure=measure)
        mv2_1 = MeasureVersionFactory(guid="guid", version="2.1", measure=measure)
        mv3_0 = MeasureVersionFactory(guid="guid", version="3.0", measure=measure)

        assert mv1_0.get_previous_version() is None
        assert mv1_1.get_previous_version() is mv1_0
        assert mv1_2.get_previous_version() is mv1_1
        assert mv2_0.get_previous_version() is mv1_2
        assert mv2_1.get_previous_version() is mv2_0
        assert mv3_0.get_previous_version() is mv2_1

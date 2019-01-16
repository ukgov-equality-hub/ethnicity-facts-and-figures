import pytest
from bs4 import BeautifulSoup
from flask import url_for

from application.cms.exceptions import RejectionImpossible
from application.cms.models import Dimension, DimensionClassification, MeasureVersion, UKCountry
from tests.utils import create_measure_versions


class TestDimensionModel:
    def test_create_valid_dimension(self, test_app_client, mock_rdu_user, stub_measure_page):
        with test_app_client.session_transaction() as session:
            session["user_id"] = mock_rdu_user.id

        data = {"title": "Test dimension"}

        url = url_for(
            "cms.create_dimension",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )

        resp = test_app_client.post(url, data=data, follow_redirects=False)

        assert resp.status_code == 302, "Should be redirected to edit page for dimension"

    def test_create_dimension_without_specifying_title(self, test_app_client, mock_rdu_user, stub_measure_page):

        with test_app_client.session_transaction() as session:
            session["user_id"] = mock_rdu_user.id

        url = url_for(
            "cms.create_dimension",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
        )

        resp = test_app_client.post(url, follow_redirects=False)

        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        assert page.find("title").string == "Error: Create dimension"

    def test_update_dimension_with_valid_data(self, db_session, test_app_client, mock_rdu_user, stub_measure_page):

        with test_app_client.session_transaction() as session:
            session["user_id"] = mock_rdu_user.id

        dimension = Dimension(
            guid="stub_dimension",
            title="Test dimension",
            time_period="stub_timeperiod",
            page=stub_measure_page,
            position=stub_measure_page.dimensions.count(),
        )

        stub_measure_page.dimensions.append(dimension)
        db_session.session.add(dimension)
        db_session.session.commit()

        data = {"title": "Test dimension"}

        url = url_for(
            "cms.edit_dimension",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
            dimension_guid=dimension.guid,
        )

        resp = test_app_client.post(url, data=data, follow_redirects=False)

        assert resp.status_code == 302, "Should be redirected to edit page for dimension"

    def test_update_dimension_with_invalid_data(self, db_session, test_app_client, mock_rdu_user, stub_measure_page):

        with test_app_client.session_transaction() as session:
            session["user_id"] = mock_rdu_user.id

        dimension = Dimension(
            guid="stub_dimension",
            title="Test dimension",
            time_period="stub_timeperiod",
            page=stub_measure_page,
            position=stub_measure_page.dimensions.count(),
        )

        stub_measure_page.dimensions.append(dimension)
        db_session.session.add(dimension)
        db_session.session.commit()

        data = {"title": ""}

        url = url_for(
            "cms.edit_dimension",
            topic_slug=stub_measure_page.parent.parent.slug,
            subtopic_slug=stub_measure_page.parent.slug,
            measure_slug=stub_measure_page.slug,
            version=stub_measure_page.version,
            dimension_guid=dimension.guid,
        )

        resp = test_app_client.post(url, data=data, follow_redirects=False)

        assert resp.status_code == 200  # TODO: this should ideally be 400.

        page = BeautifulSoup(resp.data.decode("utf-8"), "html.parser")
        assert page.find("title").string == "Error: Edit dimension"

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


class TestMeasureVersion:
    def test_publish_to_internal_review(self, stub_topic_page):
        assert stub_topic_page.status == "DRAFT"
        stub_topic_page.next_state()
        assert stub_topic_page.status == "INTERNAL_REVIEW"

    def test_publish_to_department_review(self, stub_topic_page):
        assert stub_topic_page.status == "DRAFT"
        stub_topic_page.status = "INTERNAL_REVIEW"
        stub_topic_page.next_state()
        assert stub_topic_page.status == "DEPARTMENT_REVIEW"

    def test_publish_to_approved(self, stub_topic_page):
        assert stub_topic_page.status == "DRAFT"
        stub_topic_page.status = "DEPARTMENT_REVIEW"
        stub_topic_page.next_state()
        assert stub_topic_page.status == "APPROVED"

    def test_reject_in_internal_review(self, stub_topic_page):
        stub_topic_page.status = "INTERNAL_REVIEW"
        stub_topic_page.reject()
        assert stub_topic_page.status == "REJECTED"

    def test_reject_in_department_review(self, stub_topic_page):
        stub_topic_page.status = "DEPARTMENT_REVIEW"
        stub_topic_page.reject()
        assert stub_topic_page.status == "REJECTED"

    def test_cannot_reject_approved_page(self, stub_topic_page):
        stub_topic_page.status = "APPROVED"
        with pytest.raises(RejectionImpossible):
            stub_topic_page.reject()

    def test_unpublish_page(self, stub_topic_page):
        stub_topic_page.status = "APPROVED"
        stub_topic_page.unpublish()
        assert stub_topic_page.status == "UNPUBLISH"

    def test_page_should_be_published_if_in_right_state(self, stub_measure_page):

        assert stub_measure_page.status == "DRAFT"
        assert not stub_measure_page.eligible_for_build()

        # move page to accepted state
        stub_measure_page.next_state()
        stub_measure_page.next_state()
        stub_measure_page.next_state()
        assert stub_measure_page.status == "APPROVED"

        assert stub_measure_page.eligible_for_build()

    def test_page_should_not_be_published_if_not_in_right_state(self, stub_measure_page):

        assert stub_measure_page.status == "DRAFT"

        assert not stub_measure_page.eligible_for_build()

    def test_available_actions_for_page_in_draft(self, stub_measure_page):

        expected_available_actions = ["APPROVE", "UPDATE"]

        assert stub_measure_page.status == "DRAFT"
        assert expected_available_actions == stub_measure_page.available_actions()

    def test_available_actions_for_page_in_internal_review(self, stub_measure_page):

        expected_available_actions = ["APPROVE", "REJECT"]

        stub_measure_page.status = "INTERNAL_REVIEW"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_available_actions_for_page_in_department_review(self, stub_measure_page):

        expected_available_actions = ["APPROVE", "REJECT"]

        stub_measure_page.status = "DEPARTMENT_REVIEW"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_available_actions_for_rejected_page(self, stub_measure_page):

        expected_available_actions = ["RETURN_TO_DRAFT"]

        stub_measure_page.reject()
        assert stub_measure_page.status == "REJECTED"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_available_actions_for_approved_page(self, stub_measure_page):

        expected_available_actions = ["UNPUBLISH"]

        stub_measure_page.status = "APPROVED"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_no_available_actions_for_page_awaiting_unpublication(self, stub_measure_page):

        expected_available_actions = []

        stub_measure_page.status = "UNPUBLISH"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_available_actions_for_unpublished(self, stub_measure_page):

        expected_available_actions = ["RETURN_TO_DRAFT"]

        stub_measure_page.status = "UNPUBLISHED"

        assert expected_available_actions == stub_measure_page.available_actions()

    def test_page_sort_by_version(self,):

        first_page = MeasureVersion(guid="test_page", version="1.0")
        second_page = MeasureVersion(guid="test_page", version="1.1")
        third_page = MeasureVersion(guid="test_page", version="2.0")
        fourth_page = MeasureVersion(guid="test_page", version="2.2")
        fifth_page = MeasureVersion(guid="test_page", version="2.10")
        sixth_page = MeasureVersion(guid="test_page", version="2.20")

        pages = [fourth_page, sixth_page, fifth_page, second_page, first_page, third_page]

        pages.sort()

        assert pages[0] == first_page
        assert pages[1] == second_page
        assert pages[2] == third_page
        assert pages[3] == fourth_page
        assert pages[4] == fifth_page
        assert pages[5] == sixth_page

    def test_page_has_minor_update(self, db, db_session):
        major_version = MeasureVersion(guid="test_page", version="1.0")
        minor_version = MeasureVersion(guid="test_page", version="1.1")

        db.session.add(major_version)
        db.session.add(minor_version)

        db.session.commit()

        major_version.has_minor_update()

    def test_page_has_major_update(self, db, db_session):
        major_version_1 = MeasureVersion(guid="test_page", version="1.0")
        major_version_2 = MeasureVersion(guid="test_page", version="2.0")

        db.session.add(major_version_1)
        db.session.add(major_version_2)

        db.session.commit()

        major_version_1.has_major_update()

    def test_page_has_correct_number_of_versions(self, db, db_session, stub_measure_1):
        major_version_1 = MeasureVersion(guid="test_page", version="1.0", measure_id=stub_measure_1.id)
        minor_version = MeasureVersion(guid="test_page", version="1.1", measure_id=stub_measure_1.id)
        major_version_2 = MeasureVersion(guid="test_page", version="2.0", measure_id=stub_measure_1.id)

        db.session.add(major_version_1)
        db.session.add(minor_version)
        db.session.add(major_version_2)
        db.session.commit()

        assert major_version_1.number_of_versions() == 3
        assert minor_version.number_of_versions() == 3
        assert major_version_2.number_of_versions() == 3

    def test_page_has_later_published_versions(self, db, db_session, stub_measure_1):
        major_version_1 = MeasureVersion(
            guid="test_page", version="1.0", published=True, status="APPROVED", measure_id=stub_measure_1.id
        )
        minor_version_2 = MeasureVersion(
            guid="test_page", version="1.1", published=True, status="APPROVED", measure_id=stub_measure_1.id
        )
        minor_version_3 = MeasureVersion(
            guid="test_page", version="1.2", published=True, status="APPROVED", measure_id=stub_measure_1.id
        )
        minor_version_4 = MeasureVersion(
            guid="test_page", version="1.3", published=False, status="DRAFT", measure_id=stub_measure_1.id
        )

        db.session.add(major_version_1)
        db.session.add(minor_version_2)
        db.session.add(minor_version_3)
        db.session.add(minor_version_4)
        db.session.commit()

        assert major_version_1.has_no_later_published_versions() is False
        assert minor_version_2.has_no_later_published_versions() is False
        assert minor_version_3.has_no_later_published_versions() is True
        assert minor_version_4.has_no_later_published_versions() is True

    def test_is_minor_or_minor_version(self,):
        page = MeasureVersion(guid="test_page", version="1.0")

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
    def test_measure_versions_returns_pages_ordered_by_version(
        self, db_session, stub_measure_page, stub_measure_1, page_versions, expected_order
    ):
        create_measure_versions(db_session, stub_measure_page, page_versions, parent_measure=stub_measure_1)
        assert [mv.version for mv in stub_measure_1.versions] == expected_order

    def test_measure_latest_version_returns_latest_measure_version(self, db_session, stub_measure_1):
        version_1_0 = MeasureVersion(version="1.0", guid=stub_measure_1.id, latest=False)
        version_3_1 = MeasureVersion(version="3.1", guid=stub_measure_1.id, latest=True)
        version_2_0 = MeasureVersion(version="2.0", guid=stub_measure_1.id, latest=False)
        version_3_0 = MeasureVersion(version="3.0", guid=stub_measure_1.id, latest=False)

        stub_measure_1.versions = [version_1_0, version_3_1, version_2_0, version_3_0]

        assert stub_measure_1.latest_version.version == "3.1"

    def test_measure_latest_published_version_returns_latest_published_version(self, db_session, stub_measure_1):
        version_1_0 = MeasureVersion(version="1.0", guid=stub_measure_1.id, latest=False, published=True)
        version_3_1 = MeasureVersion(version="3.1", guid=stub_measure_1.id, latest=True, published=False)
        version_2_0 = MeasureVersion(version="2.0", guid=stub_measure_1.id, latest=False, published=True)
        version_3_0 = MeasureVersion(version="3.0", guid=stub_measure_1.id, latest=False, published=True)

        stub_measure_1.versions = [version_1_0, version_3_1, version_2_0, version_3_0]

        assert stub_measure_1.latest_published_version.version == "3.0"

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
        self,
        db_session,
        page_service,
        stub_measure_page,
        page_versions,
        page_titles,
        expected_version_order,
        expected_title_order,
    ):
        create_measure_versions(db_session, stub_measure_page, page_versions, page_titles)
        db_session.session.delete(stub_measure_page)
        db_session.session.commit()

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
        page = MeasureVersion(guid="test_page", version="1.0", area_covered=countries)

        assert page.format_area_covered() == formatted_string

from datetime import datetime

import pytest

from application.auth.models import TypeOfUser
from application.cms.models import Measure
from scripts.oneoff.import_new_dimension_titles import import_dimension_titles, STANDARD_EDIT_SUMMARY
from tests.models import MeasureVersionWithDimensionFactory, UserFactory, DimensionFactory, MeasureVersionFactory


class TestImportNewDimensionTitles:
    def test_script_creates_new_measure_version_and_updates_dimension_title(self, single_use_app):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            measure__id=1,
            dimensions__guid="dimension-guid",
            dimensions__title="my dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid", "my measure", "my dimension", "my new dimension"]]

        import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert len(measure.versions) == 2
        assert measure.versions[0].version == "1.1"
        assert measure.versions[0].status == "APPROVED"
        assert measure.versions[0].dimensions[0].title == "my new dimension"
        assert measure.versions[0].external_edit_summary == STANDARD_EDIT_SUMMARY
        assert measure.versions[0].created_by == "admin@eff.gov.uk"
        assert (
            datetime.utcnow() - measure.versions[0].created_at
        ).seconds < 5, "Creation time should be within the last 5 seconds"
        assert measure.versions[0].update_corrects_data_mistake is False
        assert measure.versions[0].published_by == "admin@eff.gov.uk"
        assert measure.versions[0].published_at is None
        assert measure.versions[0].last_updated_by == "admin@eff.gov.uk"

        assert measure.versions[1].version == "1.0"
        assert measure.versions[1].dimensions[0].title == "my dimension"

    def test_script_creates_one_new_measure_version_and_updates_dimension_titles_for_two_dimensions(
        self, single_use_app, db_session
    ):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv = MeasureVersionFactory.build(
            status="APPROVED", version="1.0", title="my measure", measure__id=1, uploads=[]
        )
        mv.dimensions = [
            DimensionFactory.build(guid="dimension-guid-1", title="my dimension 1"),
            DimensionFactory.build(guid="dimension-guid-2", title="my dimension 2"),
        ]
        db_session.session.add(mv)
        db_session.session.commit()

        dimension_rows = [
            ["dimension-guid-1", "my measure", "my dimension 1", "my new dimension 1"],
            ["dimension-guid-2", "my measure", "my dimension 2", "my new dimension 2"],
        ]

        import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert len(measure.versions) == 2
        assert measure.versions[0].version == "1.1"
        assert measure.versions[0].status == "APPROVED"
        assert measure.versions[0].dimensions[0].title == "my new dimension 1"
        assert measure.versions[0].dimensions[1].title == "my new dimension 2"
        assert measure.versions[0].external_edit_summary == STANDARD_EDIT_SUMMARY

        assert measure.versions[1].version == "1.0"
        assert measure.versions[1].dimensions[0].title == "my dimension 1"
        assert measure.versions[1].dimensions[1].title == "my dimension 2"

    @pytest.mark.parametrize("new_version_state", ["REJECTED", "DRAFT", "INTERNAL_REVIEW", "DEPARTMENT_REVIEW"])
    def test_script_ignores_measure_versions_where_a_new_minor_version_already_exists(
        self, single_use_app, new_version_state
    ):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv_1_0 = MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            measure__id=1,
            dimensions__guid="dimension-guid-1.0",
            dimensions__title="my dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status=new_version_state,
            version="1.1",
            title="my measure",
            external_edit_summary=None,
            measure=mv_1_0.measure,
            dimensions__guid="dimension-guid-1.1",
            dimensions__title="my dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid-1.0", "my measure", "my dimension", "my new dimension"]]

        import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert len(measure.versions) == 2
        assert measure.versions[0].version == "1.1"
        assert measure.versions[0].status == new_version_state
        assert measure.versions[0].dimensions[0].title == "my dimension"
        assert measure.versions[0].external_edit_summary is None

        assert measure.versions[1].version == "1.0"
        assert measure.versions[1].dimensions[0].title == "my dimension"

    @pytest.mark.parametrize(
        "new_version_state", ["REJECTED", "DRAFT", "INTERNAL_REVIEW", "DEPARTMENT_REVIEW", "APPROVED"]
    )
    def test_script_creates_new_minor_version_where_new_major_version_exists(self, single_use_app, new_version_state):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv_1_0 = MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            measure__id=1,
            dimensions__guid="dimension-guid-1.0",
            dimensions__title="my dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status=new_version_state,
            version="2.0",
            title="my measure",
            external_edit_summary=None,
            measure=mv_1_0.measure,
            dimensions__guid="dimension-guid-1.1",
            dimensions__title="my dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid-1.0", "my measure", "my dimension", "my new dimension"]]

        import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert len(measure.versions) == 3
        assert measure.versions[0].version == "2.0"
        assert measure.versions[0].status == new_version_state
        assert measure.versions[0].dimensions[0].title == "my dimension"
        assert measure.versions[0].external_edit_summary is None

        assert measure.versions[1].version == "1.1"
        assert measure.versions[1].status == "APPROVED"
        assert measure.versions[1].dimensions[0].title == "my new dimension"
        assert measure.versions[1].external_edit_summary == STANDARD_EDIT_SUMMARY

        assert measure.versions[2].version == "1.0"
        assert measure.versions[2].dimensions[0].title == "my dimension"

    def test_error_count_returned_if_new_version_exists_with_different_dimension_titles(self, single_use_app):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv_1_0 = MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            measure__id=1,
            dimensions__guid="dimension-guid-1.0",
            dimensions__title="my 1.0 dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.1",
            title="my measure",
            external_edit_summary=None,
            measure=mv_1_0.measure,
            dimensions__guid="dimension-guid-1.1",
            dimensions__title="my 1.1 dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid-1.0", "my measure", "my 1.0 dimension", "my new 1.0 dimension"]]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert error_count == 1

        assert len(measure.versions) == 2
        assert measure.versions[0].version == "1.1"
        assert measure.versions[0].status == "APPROVED"
        assert measure.versions[0].dimensions[0].title == "my 1.1 dimension"
        assert measure.versions[0].external_edit_summary is None

        assert measure.versions[1].version == "1.0"
        assert measure.versions[1].dimensions[0].title == "my 1.0 dimension"

    def test_another_version_created_if_an_updated_version_is_already_approved_with_same_dimension_titles(
        self, single_use_app
    ):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv_1_0 = MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            measure__id=1,
            dimensions__guid="dimension-guid-1.0",
            dimensions__title="my dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.1",
            title="my measure",
            external_edit_summary=None,
            measure=mv_1_0.measure,
            dimensions__guid="dimension-guid-1.1",
            dimensions__title="my dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid-1.0", "my measure", "my dimension", "my new dimension"]]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert error_count == 0

        assert len(measure.versions) == 3
        assert measure.versions[0].version == "1.2"
        assert measure.versions[0].status == "APPROVED"
        assert measure.versions[0].dimensions[0].title == "my new dimension"
        assert measure.versions[0].external_edit_summary == STANDARD_EDIT_SUMMARY

        assert measure.versions[1].version == "1.1"
        assert measure.versions[1].status == "APPROVED"
        assert measure.versions[1].dimensions[0].title == "my dimension"
        assert measure.versions[1].external_edit_summary is None

        assert measure.versions[2].version == "1.0"
        assert measure.versions[2].dimensions[0].title == "my dimension"

    def test_error_count_return_if_dimension_cannot_be_found(self, single_use_app):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        MeasureVersionFactory(status="DRAFT", version="1.0", title="my measure", measure__id=1, uploads=[])
        dimension_rows = [["dimension-guid", "my measure", "my dimension", "my new dimension"]]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        assert error_count == 1

    def test_script_does_not_create_new_measure_version_if_existing_is_a_draft(self):
        pass

    def test_error_count_returned_if_new_measure_version_has_multiple_dimensions_with_the_same_title(
        self, single_use_app, db_session
    ):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv = MeasureVersionFactory.build(
            status="APPROVED", version="1.0", title="my measure", measure__id=1, uploads=[]
        )
        mv.dimensions = [
            DimensionFactory.build(guid="dimension-guid-1", title="my dimension"),
            DimensionFactory.build(guid="dimension-guid-2", title="my dimension"),
        ]
        db_session.session.add(mv)
        db_session.session.commit()

        dimension_rows = [
            ["dimension-guid-1", "my measure", "my dimension", "my dimension 1"],
            ["dimension-guid-2", "my measure", "my dimension", "my dimension 2"],
        ]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert error_count == 1
        assert len(measure.versions) == 1
        assert measure.versions[0].version == "1.0"
        assert measure.versions[0].status == "APPROVED"
        assert measure.versions[0].dimensions[0].title == "my dimension"
        assert measure.versions[0].dimensions[1].title == "my dimension"

    def test_new_measure_version_not_created_if_any_new_dimension_titles_are_blank(self, single_use_app, db_session):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv = MeasureVersionFactory.build(
            status="APPROVED", version="1.0", title="my measure", measure__id=1, uploads=[]
        )
        mv.dimensions = [
            DimensionFactory.build(guid="dimension-guid-1", title="my dimension 1"),
            DimensionFactory.build(guid="dimension-guid-2", title="my dimension 2"),
        ]
        db_session.session.add(mv)
        db_session.session.commit()

        dimension_rows = [
            ["dimension-guid-1", "my measure", "my dimension 1", ""],
            ["dimension-guid-2", "my measure", "my dimension 2", "my new dimension 2"],
        ]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert error_count == 0
        assert len(measure.versions) == 1
        assert measure.versions[0].version == "1.0"
        assert measure.versions[0].dimensions[0].title == "my dimension 1"
        assert measure.versions[0].dimensions[1].title == "my dimension 2"

    def test_new_measure_version_not_created_if_script_thinks_it_has_already_created_one(
        self, single_use_app, db_session
    ):
        user = UserFactory(user_type=TypeOfUser.ADMIN_USER, email="admin@eff.gov.uk")
        mv = MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.0",
            title="my measure",
            external_edit_summary=None,
            measure__id=1,
            dimensions__guid="dimension-guid-1.0",
            dimensions__title="my dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status="APPROVED",
            version="1.1",
            title="my measure",
            external_edit_summary=STANDARD_EDIT_SUMMARY,
            measure=mv.measure,
            dimensions__guid="dimension-guid-1.1",
            dimensions__title="my new dimension",
            uploads=[],
        )
        MeasureVersionWithDimensionFactory(
            status="DRAFT",
            version="2.0",
            title="my measure",
            external_edit_summary=None,
            measure=mv.measure,
            dimensions__guid="dimension-guid-2.0",
            dimensions__title="my dimension",
            uploads=[],
        )
        dimension_rows = [["dimension-guid-1.0", "my measure", "my dimension", "my new dimension"]]

        error_count = import_dimension_titles(user_email=user.email, app=single_use_app, dimension_rows=dimension_rows)

        measure = Measure.query.get(1)

        assert error_count == 0
        assert len(measure.versions) == 3
        assert measure.versions[0].version == "2.0"
        assert measure.versions[0].status == "DRAFT"
        assert measure.versions[0].dimensions[0].title == "my dimension"
        assert measure.versions[0].external_edit_summary is None

        assert measure.versions[1].version == "1.1"
        assert measure.versions[1].status == "APPROVED"
        assert measure.versions[1].dimensions[0].title == "my new dimension"
        assert measure.versions[1].external_edit_summary == STANDARD_EDIT_SUMMARY

        assert measure.versions[2].version == "1.0"
        assert measure.versions[2].dimensions[0].title == "my dimension"

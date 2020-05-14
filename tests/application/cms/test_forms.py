import pytest
from werkzeug.datastructures import ImmutableMultiDict


from application.cms.models import DataSource, MeasureVersion
from application.cms.forms import DataSourceForm, MeasureVersionForm

from tests.models import MeasureVersionFactory
from tests.utils import multidict_from_measure_version_and_kwargs


class TestDataSourceForm:
    def test_can_be_populated_from_data_source_object(self):
        data_source = DataSource()
        data_source.title = "blah"

        form = DataSourceForm(obj=data_source)

        assert form.title.data == data_source.title

    def test_can_populate_data_source_object_with_submitted_data(self):
        data_source = DataSource()
        form = DataSourceForm()
        form.process(formdata=ImmutableMultiDict({"title": "blah"}))

        form.populate_obj(data_source)

        assert data_source.title == form.title.data

    def test_runs_full_validation_when_sending_to_review(self):
        form = DataSourceForm(sending_to_review=True)

        form.validate()

        assert set(form.errors.keys()) == {
            "title",
            "type_of_data",
            "type_of_statistic_id",
            "publisher_id",
            "source_url",
            "frequency_of_release_id",
            "purpose",
        }


class TestMeasureVersionForm:
    def test_runs_full_validation_when_sending_to_review(self):
        form = MeasureVersionForm(is_minor_update=False, sending_to_review=True)

        form.validate()

        assert set(form.errors.keys()) == {
            "title",
            "time_covered",
            "area_covered",
            "lowest_level_of_geography_id",
            "summary",
            "measure_summary",
            "need_to_know",
            "ethnicity_definition_summary",
            "methodology",
            "external_edit_summary",
            "description",
        }

    @pytest.mark.parametrize("is_minor_update, form_should_error", ((False, False), (True, True)))
    def test_update_corrects_data_mistake_only_on_minor_versions(self, is_minor_update, form_should_error):
        form = MeasureVersionForm(is_minor_update, sending_to_review=True)

        form.validate()

        assert ("update_corrects_data_mistake" in form.errors.keys()) == form_should_error

    @pytest.mark.parametrize("is_minor_update", [False, True])
    def test_fields_populate_with_data(self, is_minor_update):
        measure_version_1_0 = MeasureVersionFactory.create(version="1.0", status="APPROVED")
        measure_version_1_1 = MeasureVersionFactory.create(
            version="1.1", measure=measure_version_1_0.measure, status="APPROVED"
        )

        form = MeasureVersionForm(
            is_minor_update=False,
            sending_to_review=True,
            obj=measure_version_1_1 if is_minor_update else measure_version_1_0,
        )

        for field in form:
            if field.name in {"update_corrects_measure_version"}:
                assert field.data is None

            elif is_minor_update is False and field.name in {"external_edit_summary", "internal_edit_summary"}:
                assert field.data == ""

            else:
                assert (
                    field.data is not None and field.data != ""
                ), f"{field.name} should be populated from the measure version"

    def test_fields_populate_with_data_when_correcting_data_mistake(self):
        measure_version_1_0 = MeasureVersionFactory.create(version="1.0", status="APPROVED")
        measure_version_1_1 = MeasureVersionFactory.create(
            version="1.1",
            measure=measure_version_1_0.measure,
            status="APPROVED",
            update_corrects_data_mistake=True,
            update_corrects_measure_version=measure_version_1_0.id,
        )

        form = MeasureVersionForm(is_minor_update=False, sending_to_review=True, obj=measure_version_1_1)

        for field in form:
            assert (
                field.data is not None and field.data != ""
            ), f"{field.name} should be populated from the measure version"

    def test_reference_field_not_populated_with_none(self):
        measure_version = MeasureVersionFactory.create(measure__reference=None)

        form = MeasureVersionForm(is_minor_update=False, sending_to_review=True, obj=measure_version)

        assert form.internal_reference.data == "", "Measure reference None should convert to empty string in the form"

    @pytest.mark.parametrize("corrects_data_mistake", [True, False])
    def test_populate_obj_doesnt_set_corrected_measure_version_if_not_correcting_a_data_mistake(
        self, corrects_data_mistake
    ):
        measure_version_1_0 = MeasureVersionFactory.create(version="1.0", status="APPROVED")
        measure_version_1_1 = MeasureVersionFactory.create(
            version="1.1",
            measure=measure_version_1_0.measure,
            status="APPROVED",
            update_corrects_data_mistake=corrects_data_mistake,
            update_corrects_measure_version=measure_version_1_0.id,
        )

        new_measure_version = MeasureVersion()

        form = MeasureVersionForm(
            is_minor_update=True,
            sending_to_review=False,
            formdata=multidict_from_measure_version_and_kwargs(measure_version_1_1),
        )

        form.populate_obj(obj=new_measure_version)

        assert new_measure_version.update_corrects_data_mistake is corrects_data_mistake

        if corrects_data_mistake:
            assert new_measure_version.update_corrects_measure_version == measure_version_1_0.id
        else:
            assert new_measure_version.update_corrects_measure_version is None

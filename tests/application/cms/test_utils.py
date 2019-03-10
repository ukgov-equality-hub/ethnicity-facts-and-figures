from flask import request, current_app, flash, render_template
from flask_wtf import FlaskForm
from lxml import html
import pytest
from wtforms.validators import DataRequired

from application.cms.forms import DataSourceForm
from application.cms.form_fields import RDUStringField
from application.cms.utils import copy_form_errors, get_data_source_forms, get_error_summary_data
from tests.models import MeasureVersionFactory


class TestCopyFormErrors:
    class FormForTest(FlaskForm):
        field = RDUStringField(label="field", validators=[DataRequired()])

    def test_copies_to_top_level_form_errors_attribute(self):
        form = self.FormForTest()
        clean_form = self.FormForTest()
        form.validate()
        assert form.errors
        assert not clean_form.errors

        copy_form_errors(from_form=form, to_form=clean_form)

        assert clean_form.errors

    def test_copies_to_field_level_errors_attribute(self):
        form = self.FormForTest()
        clean_form = self.FormForTest()
        form.validate()
        assert form.field.errors
        assert not clean_form.field.errors

        copy_form_errors(from_form=form, to_form=clean_form)

        assert clean_form.field.errors


class TestGetErrorSummaryDetails:
    class FormForTest(FlaskForm):
        field = RDUStringField(label="field", validators=[DataRequired("invalid field")])

    def test_get_error_summary_data_return_value(self):
        form = self.FormForTest()
        form.validate()

        assert get_error_summary_data(title="Form validation failed", forms=[form]) == {
            "title": "Form validation failed",
            "errors": [{"href": "#field-label", "field": "field", "text": "invalid field"}],
        }

    def test_base_template_renders_error_summary(self):
        form = self.FormForTest()
        form.validate()

        rendered_html = render_template("base.html")
        doc = html.fromstring(rendered_html)
        assert not doc.xpath("//*[contains(@class, 'govuk-error-summary')]")

        rendered_html = render_template(
            "base.html", error_summary=get_error_summary_data(title="Form validation failed", forms=[form])
        )
        doc = html.fromstring(rendered_html)
        assert doc.xpath("//*[contains(@class, 'govuk-error-summary')]")


class TestGetDataSourceForms:
    def setup(self):
        self.saved_config = {**current_app.config}

    def teardown(self):
        current_app.config = {**self.saved_config}

    def test_returns_two_data_source_forms(self):
        measure_version = MeasureVersionFactory()
        form1, form2 = get_data_source_forms(request, measure_version)

        assert isinstance(form1, DataSourceForm)
        assert isinstance(form2, DataSourceForm)

    def test_returned_forms_have_distinct_prefixes(self):
        measure_version = MeasureVersionFactory()
        form1, form2 = get_data_source_forms(request, measure_version)

        assert form1._prefix == "data-source-1-"
        assert form2._prefix == "data-source-2-"

    @pytest.mark.parametrize("csrf_enabled", [True, False])
    def test_csrf_enabled_depending_on_app_config(self, csrf_enabled):
        measure_version = MeasureVersionFactory()
        current_app.config["WTF_CSRF_ENABLED"] = csrf_enabled

        form1, form2 = get_data_source_forms(request, measure_version)

        assert form1.meta.csrf is csrf_enabled
        assert form2.meta.csrf is csrf_enabled

    def test_csrf_always_disabled_if_sending_to_review(self):
        measure_version = MeasureVersionFactory()
        current_app.config["WTF_CSRF_ENABLED"] = True

        form1, form2 = get_data_source_forms(request, measure_version, sending_to_review=True)

        assert form1.meta.csrf is False
        assert form2.meta.csrf is False


class TestFlashMessages:
    def test_markdown_rendered_in_template(self, test_app_client, logged_in_rdu_user):
        flash("text that should be markdown'd\n\n* a list item")

        doc = html.fromstring(render_template("base.html"))

        flash_message = doc.xpath("//div[@class='flash-message']")
        assert flash_message
        assert "text that should be markdown'd" in flash_message[0].text_content()
        assert flash_message[0].xpath("//li[contains(text(), 'a list item')]")

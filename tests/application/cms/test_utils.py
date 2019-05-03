from flask import request, current_app, flash, render_template
from flask_wtf import FlaskForm
from lxml import html
import pytest
from wtforms.validators import DataRequired

from application.cms.forms import DataSourceForm
from application.form_fields import RDUStringField
from application.cms.utils import copy_form_errors, get_data_source_forms, get_form_errors, ErrorSummaryMessage
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

    def test_get_errors_return_value(self):
        form = self.FormForTest()
        form.validate()

        assert get_form_errors(forms=[form]) == [ErrorSummaryMessage(href="#field-label", text="invalid field")]

    def test_get_errors_appends_extra_non_form_errors(self):
        form = self.FormForTest()
        form.validate()
        additional_error_message = ErrorSummaryMessage(href="#other-label", text="bad field")

        assert get_form_errors(forms=[form], extra_non_form_errors=[additional_error_message]) == [
            ErrorSummaryMessage(href="#field-label", text="invalid field"),
            ErrorSummaryMessage(href="#other-label", text="bad field"),
        ]

    def test_base_template_renders_error_summary(self):
        form = self.FormForTest()
        form.validate()

        rendered_html = render_template("base.html")
        doc = html.fromstring(rendered_html)
        assert not doc.xpath("//*[contains(@class, 'govuk-error-summary')]")

        rendered_html = render_template("base.html", errors=get_form_errors(forms=[form]))
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

        flash_message = doc.xpath("//div[contains(@class, 'eff-flash-message')]")
        assert flash_message
        assert "text that should be markdown'd" in flash_message[0].text_content()
        assert flash_message[0].xpath("//li[contains(text(), 'a list item')]")

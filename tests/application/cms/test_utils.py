from flask import flash, render_template
from flask_wtf import FlaskForm
from lxml import html
from wtforms.validators import DataRequired

from application.form_fields import RDUStringField
from application.cms.utils import copy_form_errors, get_form_errors, ErrorSummaryMessage


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


class TestFlashMessages:
    def test_markdown_rendered_in_template(self, test_app_client, logged_in_rdu_user):
        flash("text that should be markdown'd\n\n* a list item")

        doc = html.fromstring(render_template("base.html"))

        flash_message = doc.xpath("//div[contains(@class, 'eff-flash-message')]")
        assert flash_message
        assert "text that should be markdown'd" in flash_message[0].text_content()
        assert flash_message[0].xpath("//li[contains(text(), 'a list item')]")

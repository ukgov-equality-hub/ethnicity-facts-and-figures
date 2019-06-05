import enum
import os

from lxml import html
from unittest import mock

from flask_wtf import FlaskForm
from werkzeug.datastructures import ImmutableMultiDict
from wtforms.validators import DataRequired
import pytest

from application.form_fields import (
    _coerce_enum_to_text,
    RDUCheckboxField,
    RDURadioField,
    RDUStringField,
    RDUTextAreaField,
    RDUURLField,
    RDUPasswordField,
    RDUEmailField,
    ValidPublisherEmailAddress,
)


class TestCoerceEnumToText:
    class EnumForTest(enum.Enum):
        ONE = 1
        TWO = 2
        THREE = 3

    def test_returns_function(self):
        assert type(_coerce_enum_to_text(self.EnumForTest)).__name__ == "function"

    def test_returned_function_returns_enum_names_if_input_is_an_enum(self):
        assert _coerce_enum_to_text(self.EnumForTest)(self.EnumForTest.ONE) == "ONE"

    def test_returned_function_returns_input_if_input_is_not_an_enum(self):
        assert _coerce_enum_to_text(self.EnumForTest)("other value") == "other value"


class TestValidPublisherEmailAddress:
    class FormForTest(FlaskForm):
        email = RDUEmailField(validators=[ValidPublisherEmailAddress()])

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    @pytest.mark.parametrize(
        "valid_address",
        (
            "firstname.lastname@gov.uk",
            "firstlast@sub.gov.uk",
            "very*forgiving++£checks@sub.domain.gov.uk",
            "😊@emoji.gov.uk",
            "firstname.lastname@nhs.net",
            "firstlast@sub.nhs.net",
        ),
    )
    def test_government_emails_are_accepted(self, valid_address):
        self.form.email.data = valid_address

        assert self.form.validate() is True

    @pytest.mark.parametrize(
        "invalid_address",
        ("firstname.lastname@org.uk", "firstlast@sub.org.uk", "very*forgiving++£checks@evilgov.uk", "emoji@😊gov.uk"),
    )
    def test_non_government_emails_are_rejected(self, invalid_address):
        self.form.email.data = invalid_address

        assert self.form.validate() is False

    def test_whitelisted_emails_are_ok(self):
        self.form.email.data = "bad@email.com"
        assert self.form.validate() is False

        os.environ["ACCOUNT_WHITELIST"] = "{'bad@email.com': 'DEV_USER'}"
        assert self.form.validate() is True


class TestRDUCheckboxField:
    class FormForTest(FlaskForm):
        class EnumForTest(enum.Enum):
            ONE = "one"
            TWO = "two"
            THREE = "three"

        checkbox_field = RDUCheckboxField(label="checkbox_field", choices=[(1, "one"), (2, "two"), (3, "three")])
        checkbox_field_invalid = RDUCheckboxField(
            label="checkbox_field",
            choices=[(1, 1), (2, 2), (3, 3)],
            validators=[DataRequired(message="failed validation")],
        )
        checkbox_field_enum = RDUCheckboxField(label="checkbox_field", enum=EnumForTest)
        other_field = RDUStringField(label="other_field")

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_legend_is_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        assert doc.xpath("//legend")
        assert "checkbox_field" in doc.xpath("//legend")[0].text

    def test_checkbox_choices_are_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        assert len(doc.xpath("//input[@type='checkbox']")) == 3

    def test_checkbox_choices_have_correct_values(self):
        doc = html.fromstring(self.form.checkbox_field())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for i, checkbox in enumerate(checkboxes):
            assert checkbox.get("value") == str(self.form.checkbox_field.choices[i][0])

    def test_checkbox_can_render_choices_from_enum(self):
        doc = html.fromstring(self.form.checkbox_field_enum())

        assert len(doc.xpath("//input[@type='checkbox']")) == 3
        assert doc.xpath("//input[@type='checkbox']/following-sibling::label/text()") == ["one", "two", "three"]

    def test_checkbox_enum_choices_have_correct_values(self):
        doc = html.fromstring(self.form.checkbox_field_enum())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for checkbox, e in zip(checkboxes, [e for e in self.form.EnumForTest]):
            assert checkbox.get("value") == e.name
            assert checkbox.xpath("following-sibling::label")[0].text == e.value

    def test_checkbox_labels_are_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for i, checkbox in enumerate(checkboxes):
            label = checkbox.xpath("following-sibling::label")[0]
            assert label.text == self.form.checkbox_field.choices[i][1]

    @pytest.mark.parametrize("disabled", [True, False])
    def test_render_field_with_disabled_causes_all_inputs_to_be_disabled(self, disabled):
        doc = html.fromstring(self.form.checkbox_field(disabled=disabled))

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for checkbox in checkboxes:
            assert checkbox.get("disabled") == ("disabled" if disabled else None)

    def test_can_be_rendered_block_or_inline(self):
        doc = html.fromstring(self.form.checkbox_field(inline=False))
        checkboxes_div = doc.xpath("//div[contains(@class, 'govuk-checkboxes')]")[0]
        assert "govuk-checkboxes--inline" not in checkboxes_div.attrib["class"]

        doc = html.fromstring(self.form.checkbox_field(inline=True))
        checkboxes_div = doc.xpath("//div[contains(@class, 'govuk-checkboxes')]")[0]
        assert "govuk-checkboxes--inline" in checkboxes_div.attrib["class"]


class TestRDURadioField:
    class FormForTest(FlaskForm):
        radio_field = RDURadioField(label="radio_field", choices=[(1, "one"), (2, "two"), (3, "three")])
        radio_field_invalid = RDURadioField(
            label="radio_field",
            choices=[(1, 1), (2, 2), (3, 3)],
            validators=[DataRequired(message="failed validation")],
        )
        other_field = RDUStringField(label="other_field")

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_legend_is_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        assert doc.xpath("//legend")
        assert "radio_field" in doc.xpath("//legend")[0].text

    def test_legend_class_is_rendered(self):
        # TODO: I really test FormGroups, not just radio fields. should be split out into separate test class for them.
        doc = html.fromstring(self.form.radio_field(legend_class="govuk-!-font-weight-bold"))

        assert doc.xpath("//legend")
        assert doc.xpath("//legend/@class")[0] == "govuk-fieldset__legend govuk-!-font-weight-bold"

    def test_radio_choices_are_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        assert len(doc.xpath("//input[@type='radio']")) == 3

    def test_radio_choices_have_correct_values(self):
        doc = html.fromstring(self.form.radio_field())

        radios = doc.xpath("//input[@type='radio']")
        for i, radio in enumerate(radios):
            assert radio.get("value") == str(self.form.radio_field.choices[i][0])

    def test_radio_labels_are_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        radios = doc.xpath("//input[@type='radio']")
        for i, radio in enumerate(radios):
            label = radio.xpath("following-sibling::label")[0]
            assert label.text == self.form.radio_field.choices[i][1]

    @pytest.mark.parametrize("disabled", [True, False])
    def test_render_field_with_disabled_causes_all_inputs_to_be_disabled(self, disabled):
        doc = html.fromstring(self.form.radio_field(disabled=disabled))

        radios = doc.xpath("//input[@type='radio']")
        for radio in radios:
            assert radio.get("disabled") == ("disabled" if disabled else None)

    def test_other_field_is_rendered(self):
        self.form.radio_field.set_other_field(self.form.other_field)
        doc = html.fromstring(self.form.radio_field())

        assert len(doc.xpath("//input[@type='text']")) == 1

    def test_other_field_includes_show_hide_script(self):
        self.form.radio_field.set_other_field(self.form.other_field)
        doc = html.fromstring(self.form.radio_field())

        assert "showHideControl" in doc.xpath("//script")[0].text

    def test_can_be_rendered_block_or_inline(self):
        doc = html.fromstring(self.form.radio_field(inline=False))
        radios_div = doc.xpath("//div[contains(@class, 'govuk-radios')]")[0]
        assert "govuk-radios--inline" not in radios_div.attrib["class"]

        doc = html.fromstring(self.form.radio_field(inline=True))
        radios_div = doc.xpath("//div[contains(@class, 'govuk-radios')]")[0]
        assert "govuk-radios--inline" in radios_div.attrib["class"]


class TestRDUStringField:
    class FormForTest(FlaskForm):
        string_field = RDUStringField(label="string_field", hint="string_field hint")
        string_field_invalid = RDUStringField(
            label="string_field", hint="string_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.string_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.string_field())

        assert doc.xpath("//input[@type='text']")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.string_field())

        assert not self.form.string_field.errors
        assert doc.xpath("//*[text()='string_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.string_field_invalid())

        assert self.form.string_field_invalid.errors
        assert doc.xpath("//*[text()='string_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.string_field_invalid())

        assert self.form.string_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"string_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.string_field == "some data"

    def test_populates_obj_with_none_if_value_is_empty_string(self):
        formdata = ImmutableMultiDict({"string_field": ""})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.string_field is None

    def test_strips_leading_and_trailing_whitespace(self):
        formdata = ImmutableMultiDict({"string_field": "   blah   \n\n   blah   "})
        self.form.process(formdata=formdata)

        assert self.form.string_field.data == "blah   \n\n   blah"


class TestRDUPasswordField:
    class FormForTest(FlaskForm):
        password_field = RDUPasswordField(label="password_field", hint="password_field hint")
        password_field_invalid = RDUPasswordField(
            label="password_field", hint="password_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.password_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.password_field())

        assert doc.xpath("//input[@type='password']")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.password_field())

        assert not self.form.password_field.errors
        assert doc.xpath("//*[text()='password_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.password_field_invalid())

        assert self.form.password_field_invalid.errors
        assert doc.xpath("//*[text()='password_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.password_field_invalid())

        assert self.form.password_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"password_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.password_field == "some data"

    def test_does_not_strip_leading_and_trailing_whitespace(self):
        formdata = ImmutableMultiDict({"password_field": "   blah   \n\n   blah   "})
        self.form.process(formdata=formdata)

        assert self.form.password_field.data == "   blah   \n\n   blah   "


class TestRDUURLField:
    class FormForTest(FlaskForm):
        url_field = RDUURLField(label="url_field", hint="url_field hint")
        url_field_invalid = RDUURLField(
            label="url_field", hint="url_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.url_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.url_field())

        assert doc.xpath("//input[@type='url']")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.url_field())

        assert not self.form.url_field.errors
        assert doc.xpath("//*[text()='url_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.url_field_invalid())

        assert self.form.url_field_invalid.errors
        assert doc.xpath("//*[text()='url_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.url_field_invalid())

        assert self.form.url_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"url_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.url_field == "some data"

    def test_strips_leading_and_trailing_whitespace(self):
        formdata = ImmutableMultiDict({"url_field": "   blah   \n\n   blah   "})
        self.form.process(formdata=formdata)

        assert self.form.url_field.data == "blah   \n\n   blah"


class TestRDUTextAreaField:
    class FormForTest(FlaskForm):
        textarea_field = RDUTextAreaField(label="textarea_field", hint="textarea_field hint", character_count_limit=130)
        textarea_field_invalid = RDUTextAreaField(
            label="textarea_field", hint="textarea_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.textarea_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.textarea_field())

        assert doc.xpath("//textarea")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.textarea_field())

        assert not self.form.textarea_field.errors
        assert doc.xpath("//*[text()='textarea_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.textarea_field_invalid())

        assert self.form.textarea_field_invalid.errors
        assert doc.xpath("//*[text()='textarea_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.textarea_field_invalid())

        assert self.form.textarea_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"textarea_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.textarea_field == "some data"

    def test_character_count_information_is_shown(self):
        doc = html.fromstring(self.form.textarea_field())

        character_count_element = doc.xpath('//span[@id="textarea_field-info"]')

        assert len(character_count_element) == 1
        assert character_count_element[0].text == "Please try to keep within 130 characters."
        assert {"govuk-hint", "govuk-character-count__message"} <= set(
            character_count_element[0].get("class", "").split()
        )
        assert character_count_element[0].get("aria-live") == "polite"

    def test_character_count_javascript_is_enabled(self):
        doc = html.fromstring(self.form.textarea_field())

        govuk_char_count_element = doc.xpath("//*[@class='govuk-character-count']")
        assert len(govuk_char_count_element) == 1
        assert govuk_char_count_element[0].get("data-module") == "character-count"
        assert govuk_char_count_element[0].get("data-maxlength") == "130"

        textarea = doc.xpath("//textarea")[0]
        assert {"govuk-textarea", "js-character-count"} <= set(textarea.get("class", "").split())

    def test_strips_whitespace_from_start_and_end_of_text_and_start_of_each_line(self):
        formdata = ImmutableMultiDict({"textarea_field": "   blah   \n\n   blah   "})
        self.form.process(formdata=formdata)

        assert self.form.textarea_field.data == "blah   \n\nblah"

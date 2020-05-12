import pytest

from application.cms.filters import html_line_breaks
from application.static_site.filters import render_markdown
from application.static_site.filters import html_params


class TestRenderMarkdown:
    @pytest.mark.parametrize(
        "input_text, expected_output",
        (
            ("hello", '<p class="govuk-body">hello</p>'),
            ("* blah", '<ul class="govuk-list govuk-list--bullet eff-list--sparse">\n<li>blah</li>\n</ul>'),
        ),
    )
    def test_markdown_is_expanded(self, input_text, expected_output):
        assert render_markdown(input_text) == expected_output

    @pytest.mark.parametrize(
        "input_text, expected_output",
        (("<script>alert(1);</script>", '<p class="govuk-body">&lt;script&gt;alert(1);&lt;/script&gt;</p>'),),
    )
    def test_html_is_escaped(self, input_text, expected_output):
        assert render_markdown(input_text) == expected_output

    @pytest.mark.parametrize(
        "input_text, expected_output",
        (
            (
                "[text to display](javascript:alert(1))",
                '<p class="govuk-body"><a class="govuk-link" href="#">text to display</a></p>',
            ),
            (
                "[text to display](https://gov.uk)",
                '<p class="govuk-body"><a class="govuk-link" href="https://gov.uk">text to display</a></p>',
            ),
            (
                "[text to display](https://javascript.co.uk)",
                '<p class="govuk-body"><a class="govuk-link" href="https://javascript.co.uk">text to display</a></p>',
            ),
        ),
    )
    def test_js_links_stripped(self, input_text, expected_output):
        assert render_markdown(input_text) == expected_output


class TestHtmlParams:
    """
    html_params is a helper filter which converts a Python dictionary into
    HTML attributes for output.
    """

    def test_params_are_converted_into_ordered_html_attributes(self):
        output = html_params({"value": "Test", "aria-controls": "blah"})
        assert output == 'aria-controls="blah" value="Test"'

    def test_boolean_params_are_converted_into_boolean_attributes(self):
        assert html_params({"disabled": True}) == "disabled"

    def test_double_quotes_are_escaped(self):
        assert html_params({"value": 'Escape "me"'}) == 'value="Escape &#34;me&#34;"'

    def test_ampersand_is_escaped(self):
        output = html_params({"href": "/?a&b"})
        assert output == 'href="/?a&amp;b"'

    def test_less_than_and_greater_than_is_escaped(self):
        output = html_params({"query": "a < b > c"})
        assert output == 'query="a &lt; b &gt; c"'


class TestHtmlLineBreaks:
    @pytest.mark.parametrize(
        "input_text, expected_output",
        (("hello", "hello"), ("* blah\n* rhubarb\n* waffle", "* blah<br />* rhubarb<br />* waffle")),
    )
    def test_line_breaks_become_br_tags(self, input_text, expected_output):
        assert html_line_breaks(input_text) == expected_output

    @pytest.mark.parametrize(
        "input_text, expected_output",
        (("* blah<script>alert(1);</script>\n* waffle", "* blah&lt;script&gt;alert(1);&lt;/script&gt;<br />* waffle"),),
    )
    def test_other_html_is_escaped(self, input_text, expected_output):
        assert html_line_breaks(input_text) == expected_output

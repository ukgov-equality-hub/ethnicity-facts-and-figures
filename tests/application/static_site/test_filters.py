import pytest

from application.static_site.filters import render_markdown


class TestRenderMarkdown:
    @pytest.mark.parametrize(
        "input_text, expected_output",
        (
            ("hello", '<p class="govuk-body">hello</p>'),
            ("* blah", '<ul class="govuk-list govuk-list--bullet">\n<li>blah</li>\n</ul>'),
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

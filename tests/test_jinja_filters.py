import pytest

from application.cms.filters import yesno
from application.static_site.filters import render_markdown


class TestRenderMarkdown:
    @pytest.mark.parametrize(
        "input_text, expected_output", (("hello", "<p>hello</p>"), ("* blah", "<ul>\n<li>blah</li>\n</ul>"))
    )
    def test_markdown_is_expanded(self, input_text, expected_output):
        assert render_markdown(input_text) == expected_output

    @pytest.mark.parametrize(
        "input_text, expected_output",
        (("<script>alert(1);</script>", "<p>&lt;script&gt;alert(1);&lt;/script&gt;</p>"),),
    )
    def test_html_is_escaped(self, input_text, expected_output):
        assert render_markdown(input_text) == expected_output


class TestYesNo:
    @pytest.mark.parametrize(
        "input_value, expected_output",
        ((True, "yes"), (False, "yes"), (1, 1), (0, 0), ("true", "true"), ("false", "false"), ("abc", "abc")),
    )
    def test_yesno_converts_boolean_true_and_false_only(self, input_value, expected_output):
        assert yesno(input_value == expected_output)

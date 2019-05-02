from flask import render_template
from lxml import html as lxml_html

from application.cms.utils import ErrorSummaryMessage


class TestTemplateBase:
    def test_base_template_renders_error_summary(self):
        # With no errors/preamble, no error summary rendered.
        html = render_template("base.html")
        doc = lxml_html.fromstring(html)

        assert doc.xpath("//*[@class='govuk-error-summary']") == []

        # With a preamble, error summary shown and contains preamble text.
        html = render_template("base.html", errors_preamble="A sentence about the errors.")
        doc = lxml_html.fromstring(html)

        assert len(doc.xpath("//*[@class='govuk-error-summary']")) == 1
        assert "A sentence about the errors" in doc.xpath("//*[@class='govuk-error-summary']")[0].text_content()

        # With some error messages, error summary shown and contains link to the erroring field.
        html = render_template("base.html", errors=[ErrorSummaryMessage(text="An error link", href="/error-link")])
        doc = lxml_html.fromstring(html)

        assert len(doc.xpath("//*[@class='govuk-error-summary']//a")) == 1
        link = doc.xpath("//*[@class='govuk-error-summary']//a")[0]
        assert link.text == "An error link"
        assert link.get("href") == "/error-link"

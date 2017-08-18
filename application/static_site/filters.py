from flask import Markup
from hurry.filesize import size, alternative
import markdown
import jinja2


def render_markdown(string):
    return Markup(markdown.markdown(string))


def breadcrumb_friendly(slug):
    s = slug.replace('-', ' ')
    return s.capitalize()


def filesize(string):
    try:
        return size(int(string), system=alternative)
    except TypeError:
        return string


def value_filter(value):

    icon_html = {
      "N/A": "<span class=\"not-applicable\">N/A<sup>*</sup></span>",
      "?": __missing_data_icon("sample-too-small") +
      __icon_explanation("withheld because a small sample size makes it unreliable"),
      "!": __missing_data_icon("confidential") +
      __icon_explanation("withheld to protect confidentiality"),
      "-": __missing_data_icon("not-collected") +
      __icon_explanation("not collected")
    }

    if value in icon_html:
        return icon_html[value]
    else:
        return jinja2.escape(value)


def __missing_data_icon(class_name):
    return "<span class=\"missing-data " + class_name + "\"></span>"


def __icon_explanation(explanation):
    return "<span class=\"visually-hidden\">" + explanation + "</span>"

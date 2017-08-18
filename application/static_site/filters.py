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
      "?": "<span class=\"missing-data sample-too-small\"><span class=\"visually-hidden\">withheld because a small sample size makes it unreliable</span></span>",
      "!": "<span class=\"missing-data confidential\"><span class=\"visually-hidden\">withheld to protect confidentiality</span></span>",
      "-": "<span class=\"missing-data not-collected\"><span class=\"visually-hidden\">not collected</span></span>"
    }

    if value in icon_html:
        return icon_html[value]
    else:
        return jinja2.escape(value)
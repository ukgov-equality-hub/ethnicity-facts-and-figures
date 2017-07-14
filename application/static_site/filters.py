from flask import Markup
from hurry.filesize import size, alternative
import markdown


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

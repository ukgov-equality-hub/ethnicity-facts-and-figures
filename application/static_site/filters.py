from flask import Markup
import markdown


def render_markdown(string):
    return Markup(markdown.markdown(string))


def breadcrumb_friendly(slug):
    s = slug.replace('-', ' ')
    return s.capitalize()

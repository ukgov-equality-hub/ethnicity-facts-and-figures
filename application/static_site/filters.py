from flask import Markup
import markdown


def render_markdown(string):
    return Markup(markdown.markdown(string))

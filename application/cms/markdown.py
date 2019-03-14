from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class DesignSystemMarkdownProcessor(Treeprocessor):
    def run(self, root):
        for p in root.iter("p"):
            p.set("class", "govuk-body")

        for a in root.iter("a"):
            a.set("class", "govuk-link")

        for ul in root.iter("ul"):
            ul.set("class", "govuk-list govuk-list--bullet")

        for ol in root.iter("ol"):
            ol.set("class", "govuk-list govuk-list--number")


class DesignSystemMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(item=DesignSystemMarkdownProcessor(md), name="design-system-markdown", priority=0)


def markdown(text):
    md = Markdown(extensions=[DesignSystemMarkdownExtension()])
    return md.convert(text)

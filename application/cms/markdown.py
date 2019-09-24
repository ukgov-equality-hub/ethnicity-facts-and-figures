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
            ul.set("class", "govuk-list govuk-list--bullet eff-list--sparse")

        for ol in root.iter("ol"):
            ol.set("class", "govuk-list govuk-list--number eff-list--sparse")


class MarkdownCleanerProcessor(Treeprocessor):
    def run(self, root):
        for a in root.iter("a"):
            if "javascript:" in a.get("href"):
                a.set("href", "#")


class DesignSystemMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(item=DesignSystemMarkdownProcessor(md), name="design-system-markdown", priority=0)
        md.treeprocessors.register(item=MarkdownCleanerProcessor(md), name="cleaner-markdown", priority=0)


def markdown(text):
    md = Markdown(extensions=[DesignSystemMarkdownExtension()])
    return md.convert(text)

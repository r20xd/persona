"""Restricted assistant-only Markdown. Raw session/API content is never rewritten."""

from html import escape

from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML

register = template.Library()


class TextOnlyLinksRenderer(RendererHTML):
    """Parse useful labels, but never emit an anchor, image or its attributes."""

    def link_open(self, tokens, idx, options, env):
        return ""

    def link_close(self, tokens, idx, options, env):
        return ""

    def image(self, tokens, idx, options, env):
        label = self.renderInlineAsText(tokens[idx].children, options, env)
        return escape(label)


# Raw HTML/autolinks/linkify are off. Explicit links/images produce only their
# escaped labels through the fixed renderer, never href/src or other attributes.
MARKDOWN = MarkdownIt(
    "commonmark",
    {"html": False, "linkify": False},
    renderer_cls=TextOnlyLinksRenderer,
).disable(["autolink"])


@register.filter
def assistant_markdown(value):
    tokens = MARKDOWN.parse(str(value))
    for token in tokens:
        if token.type in {"heading_open", "heading_close"}:
            # Page h1 > chat h2 > message h3 > generated content h4/h5/h6.
            token.tag = f"h{min(6, int(token.tag[1:]) + 3)}"
    # Safe only because the fixed parser/renderer cannot emit untrusted HTML/URL attributes;
    # text and code are escaped by markdown-it, with no highlighter/plugins.
    return mark_safe(MARKDOWN.renderer.render(tokens, MARKDOWN.options, {}))

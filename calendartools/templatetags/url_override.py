from django import template
from django.template.defaulttags import URLNode as OrigURLNode
from django.template.defaulttags import url as orig_url
from django.utils import translation

register = template.Library()

class URLNode(OrigURLNode):
    """Overrides urls to avoid translation."""

    def render(self, context):
        language = translation.get_language()
        translation.deactivate()
        resolved_url = super(URLNode, self).render(context)
        translation.activate(language)
        return resolved_url

def url(parser, token):
    n = orig_url(parser, token)
    return URLNode(n.view_name, n.args, n.kwargs, n.asvar)

url = register.tag(url)

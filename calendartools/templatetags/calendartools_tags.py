from django import template
from django.utils import translation

register = template.Library()

# Unused:
# ------------------------------------------------------------

@register.filter(name='divide_by')
def divide_by(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return ''
divide_by.is_safe = True

@register.filter(name='to_integer')
def to_integer(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return ''
to_integer.is_safe = True

@register.filter(name='range')
def make_range(arg1, arg2=None):
    """Produces inclusive range"""
    if not arg2:
        return range(arg1)
    else:
        return range(arg1, arg2)
make_range.is_safe = True

@register.filter(name='get_index')
def get_index(container, index):
    return container[index]

# ------------------------------------------------------------

@register.filter
def columns(lst, cols):
    """
    Break a list into ``n`` lists, typically for use in columns.
    Sources:
        http://brandonkonkle.com/blog/2010/may/26/snippet-django-columns-filter/
        http://herself.movielady.net/2008/07/16/split-list-to-columns-django-template-tag/

    >>> lst = range(10)
    >>> for list in columns(lst, 3):
    ...     list
    [0, 1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]
    """
    try:
        cols = int(cols)
        lst = list(lst)
    except (ValueError, TypeError):
        raise StopIteration()

    start = 0
    for i in xrange(cols):
        stop = start + len(lst[i::cols])
        yield lst[start:stop]
        start = stop


def force_no_translation(parser, token):
    nodelist = parser.parse(('endnotrans',))
    parser.delete_first_token()
    return NoTransNode(nodelist)

class NoTransNode(template.Node):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        language = translation.get_language()
        translation.deactivate()
        output = self.nodelist.render(context)
        translation.activate(language)
        return output

register.tag('notrans', force_no_translation)

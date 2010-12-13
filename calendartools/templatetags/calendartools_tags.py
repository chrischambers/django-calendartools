from django import template
from django.template.defaultfilters import stringfilter
from django.utils import translation

register = template.Library()

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

def do_no_translation(value, arg=None):
    language = translation.get_language()
    translation.deactivate()
    value = value[:] # force evaluation of django.utils.__proxy__ obj
    translation.activate(language)
    return value
do_no_translation.is_safe = True

register.tag('notrans', force_no_translation)
register.filter('notrans', do_no_translation)


from urlparse import urlparse
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs
from urllib import urlencode

@register.filter(name='clear_query_string')
@stringfilter
def clear_query_string(url):
    parsed_url = urlparse(url)
    new_url = parsed_url.path
    if parsed_url[0] and parsed_url[1]:
        new_url = "%s://%s%s" % (
            parsed_url.scheme, parsed_url.hostname,
            new_url
        )
    return new_url

@register.filter(name='set_query_string')
@stringfilter
def set_query_string_wrapper(url, arg):
    """
    Temporary fix until template filters take multiple arguments:
    http://code.djangoproject.com/ticket/1199#comment:16
    """
    try:
        key, value = arg.split(',')
        return set_query_string(url, key, value)
    except ValueError:
        return ""

def set_query_string(url, key, value):
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    querydict[key] = value
    newquery = urlencode(querydict, doseq=True)
    new_url = "%s?%s%s" % (
        parsed_url.path, newquery, parsed_url.fragment
    )
    if parsed_url[0] and parsed_url[1]:
        new_url = "%s://%s%s" % (
            parsed_url.scheme, parsed_url.hostname,
            new_url
        )
    return new_url

@register.filter(name='get_query_string')
@stringfilter
def get_query_string(url, key):
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    return querydict.get(key, '')

@register.filter(name='delete_query_string')
@stringfilter
def delete_query_string(url, key):
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    querydict.pop(key, None)
    if querydict:
        newquery = urlencode(querydict, doseq=True)
        new_url = "%s?%s%s" % (
            parsed_url.path, newquery, parsed_url.fragment
        )
    else:
        new_url = parsed_url.path
    if parsed_url[0] and parsed_url[1]:
        new_url = "%s://%s%s" % (
            parsed_url.scheme, parsed_url.hostname,
            new_url
        )
    return new_url

@register.filter()
def time_relative_to_today(dt):
    from calendartools.periods import Day
    from datetime import datetime
    today = Day(datetime.now())
    if dt < today:
        return 'past'
    elif dt in today:
        return 'today'
    else:
        return 'future'

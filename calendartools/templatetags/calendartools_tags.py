from django import template
from django.template.defaultfilters import stringfilter
from django.utils import translation
from threaded_multihost.threadlocals import get_current_request

register = template.Library()

@register.filter
def columns(lst, cols, pad_columns=True, filler=None):
    """
    Break a list into ``n`` lists, typically for use in columns.
    Sources:
        http://brandonkonkle.com/blog/2010/may/26/snippet-django-columns-filter/
        http://herself.movielady.net/2008/07/16/split-list-to-columns-django-template-tag/

    >>> lst = range(10)
    >>> for list in columns(lst, 3, pad_columns=False):
    ...     list
    [0, 1, 2, 3]
    [4, 5, 6, 7]
    [8, 9]

    >>> for list in columns(lst, 3, filler=0):
    ...     list
    [0, 1, 2, 3]
    [4, 5, 6, 7]
    [8, 9, 0, 0]

    If ``pad_columns`` is truthy, the remaining column will be padded with the
    ``filler`` parameter until it is equal in length to the previous ones.
    """
    try:
        cols = int(cols)
        lst = list(lst)
    except (ValueError, TypeError):
        raise StopIteration()

    start = 0
    length = 0
    for i in xrange(cols):
        length = max(length, len(lst[i::cols]))
        stop = start + length
        sliced = lst[start:stop]
        if pad_columns:
            padding = length - len(sliced)
            if padding:
                for j in xrange(padding):
                    sliced.append(filler)
        yield sliced
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

@register.filter(name='get_query_string')
@stringfilter
def get_query_string(url, key):
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    return querydict.get(key, '')

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
    """
    Also has the side effect of sorting the query-string parameter keys.
    """
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    querydict[key] = value
    newquery = urlencode(sorted(querydict.items()), doseq=True)
    new_url = "%s?%s%s" % (
        parsed_url.path, newquery, parsed_url.fragment
    )
    if parsed_url[0] and parsed_url[1]:
        new_url = "%s://%s%s" % (
            parsed_url.scheme, parsed_url.hostname,
            new_url
        )
    return new_url


class SetQueryStringNode(template.Node):
    def __init__(self, url, key, value, varname):
        self.url = template.Variable(url)
        self.key = key
        self.value = template.Variable(value)
        self.varname = varname

    def render(self, context):
        url = self.url.resolve(context)
        value = self.value.resolve(context)
        context[self.varname] = set_query_string(
            url, self.key, value
        )
        return ''

def do_set_query_string(parser, token):
    try:
        tag_name, url, key, value, as_, varname = token.split_contents()
    except ValueError, e:
        raise template.TemplateSyntaxError("%r requires 6 arguments" % (
                token.contents.split()[0],
        ))
    return SetQueryStringNode(url, key, value, varname)

register.tag('set_query_string', do_set_query_string)

@register.filter(name='delete_query_string')
@stringfilter
def delete_query_string(url, key):
    """
    Also has the side effect of sorting the query-string parameter keys.
    """
    parsed_url = urlparse(url)
    querydict = parse_qs(parsed_url.query)
    querydict.pop(key, None)
    if querydict:
        newquery = urlencode(sorted(querydict.items()), doseq=True)
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

@register.filter(name='persist_query_string')
@stringfilter
def persist_query_string(url, from_url=None):
    """
    Transfers GET parameters from ``from_url`` to ``url`` as *defaults* (if
    ``url`` has a different value for that GET parameter, it will
    remain as-is).

    Also has the side effect of sorting the query-string parameter keys.
    """
    from_url = from_url or get_current_request().get_full_path()
    parsed_url = urlparse(from_url)
    querydict = parse_qs(parsed_url.query)
    if not querydict:
        return url
    else:
        parsed_new_url = urlparse(url)
        querydict.update(parse_qs(parsed_new_url.query))
        newquery = urlencode(sorted(querydict.items()), doseq=True)
        new_url = "%s?%s%s" % (
            parsed_new_url.path, newquery, parsed_new_url.fragment
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


class DiggPaginationNode(template.Node):
    def __init__(self, page, varname):
        self.page = template.Variable(page)
        self.varname = varname
        self.max_range = 5

    def render(self, context):
        page = self.page.resolve(context)
        current = page.number - 1 # pages are 1-indexed.
        start, end = current - self.max_range, current + self.max_range
        if start < 0:
            start = 0
        page_list = page.paginator.page_range[start:end]
        context[self.varname] = page_list
        return ''

def do_digg_pagination(parser, token):
    try:
        tag_name, page, as_, varname = token.split_contents()
    except ValueError, e:
        raise template.TemplateSyntaxError("%r requires 4 arguments" % (
                token.contents.split()[0],
        ))
    return DiggPaginationNode(page, varname)

register.tag('digg_pagination', do_digg_pagination)

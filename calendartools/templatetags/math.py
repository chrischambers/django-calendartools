from django import template

register = template.Library()

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

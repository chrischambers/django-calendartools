from calendartools.periods.proxybase import LocalizedSimpleProxy
from django.conf import settings
from timezones.utils import localtime_for_timezone
import pytz

try:
    from functools import partial
except ImportError: # Python 2.3, 2.4 fallback.
    from django.utils.functional import curry as partial

def timedelta_to_total_seconds(timedelta):
    '''
    Calculate the total number of seconds represented by a
    ``datetime.timedelta`` object.

    >>> from datetime import timedelta
    >>> timedelta_to_total_seconds(timedelta(0))
    0
    >>> timedelta_to_total_seconds(timedelta(1))
    86400
    >>> timedelta_to_total_seconds(timedelta(days=1, seconds=10))
    86410
    >>> timedelta_to_total_seconds(timedelta(days=1, hours=1))
    90000
    >>> timedelta_to_total_seconds(timedelta(hours=1, seconds=10))
    3610
    '''
    return int(timedelta.total_seconds())

import calendar
DAY_MAP = [
    calendar.SUNDAY,
    calendar.MONDAY,
    calendar.TUESDAY,
    calendar.WEDNESDAY,
    calendar.THURSDAY,
    calendar.FRIDAY,
    calendar.SATURDAY,
]
def standardise_first_dow(first_day_of_week=None):
    """
    Django's FIRST_DAY_OF_WEEK setting runs from 0-6, Sunday through Saturday
    (American Convention - apparently for implementation reasons, see:
    http://code.djangoproject.com/ticket/1061). Python's datetime, dateutil and
    calendar modules all use 0-6, Monday through Sunday. This function infers
    the 'standardised' version from the django setting.
    >>> from django.conf import settings
    >>> settings.FIRST_DAY_OF_WEEK = 0 # Sunday
    >>> standardise_first_dow()
    6
    >>> settings.FIRST_DAY_OF_WEEK = 1 # Monday
    >>> standardise_first_dow()
    0
    >>> settings.FIRST_DAY_OF_WEEK = 6 # Saturday
    >>> standardise_first_dow()
    5
    """
    if not first_day_of_week:
        first_day_of_week = settings.FIRST_DAY_OF_WEEK
    return DAY_MAP[first_day_of_week]


class LocalizedOccurrenceProxy(LocalizedSimpleProxy):
    """A proxy whose ultimate goal is to make working with non-naive datetimes
    a seamless experience, especially for template authors.
    """
    def __init__(self, obj, *args, **kwargs):
        if isinstance(obj, self.__class__):
            obj = obj._obj
        super(LocalizedOccurrenceProxy, self).__init__(obj, *args, **kwargs)

    def _get_datetime_attr(self, attrname):
        dt = getattr(self._obj, attrname)
        return localtime_for_timezone(dt, self.timezone)

    def _set_datetime_attr(self, value, attrname):
        if value.tzinfo is not None:
            value = value.astimezone(self.default_timezone).replace(tzinfo=None)
        setattr(self._obj, attrname, value)

    def _datetime_attr_doc(self, attrname):
        return getattr(self._obj, attrname).__doc__

    start = property(
        fget=partial(_get_datetime_attr, attrname='start'),
        fset=partial(_set_datetime_attr, attrname='start'),
        doc= partial(_datetime_attr_doc, attrname='start')
    )
    finish = property(
        fget=partial(_get_datetime_attr, attrname='finish'),
        fset=partial(_set_datetime_attr, attrname='finish'),
        doc= partial(_datetime_attr_doc, attrname='finish')
    )

    @property
    def real_start(self):
        return self._obj.start

    @property
    def real_finish(self):
        return self._obj.finish

    @property
    def default_timezone(self):
        return pytz.timezone(settings.TIME_ZONE)

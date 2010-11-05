from django.views.generic import simple
from django.core.urlresolvers import reverse

import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, YEARLY, MONTHLY, DAILY, HOURLY

class SimpleProxy(object):
    def __init__(self, obj, *args, **kwargs):
        self._obj = obj
        super(SimpleProxy, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return unicode(self._obj)

    def __repr__(self):
        try:
            u = unicode(self)
        except (UnicodeEncodeError, UnicodeDecodeError):
            u = '[Bad Unicode data]'
        return (u'<%s: %s>' % (self.__class__.__name__, u)).encode('utf8')

    def __getattr__(self, attr):
        try:
            return getattr(self.__class__, attr)
        except AttributeError:
            return getattr(self._obj, attr)


class DateTimeProxy(SimpleProxy):
    def previous(self):
        return self._obj - self.interval

    def next(self):
        return self._obj + self.interval


class Day(DateTimeProxy):
    interval = relativedelta(days=+1)

    def __iter__(self):
        start = datetime(self.year, self.month, self.day)
        finish = start + timedelta(1) - timedelta.resolution
        return (dt for dt in rrule(HOURLY, dtstart=start, until=finish))

class Month(DateTimeProxy):
    interval = relativedelta(months=+1)

    def __iter__(self):
        last_day = calendar.monthrange(self.year, self.month)[-1]
        return (dt for dt in rrule(DAILY,
            dtstart=self.replace(day=1),
            until=self.replace(day=last_day)
        ))

class Year(DateTimeProxy):
    interval = relativedelta(years=+1)

    def __iter__(self):
        return (dt for dt in rrule(MONTHLY,
            dtstart=self.replace(day=1, month=1),
            until=self.replace(day=31, month=12)
        ))

class Calendar(object):

    def __init__(self, start, finish, occurrences=None, *args, **kwargs):
        self.start  = start
        self.finish = finish
        self.occurrences = occurrences or []
        super(Calendar, self).__init__(*args, **kwargs)

    def __iter__(self):
        return self.years

    @property
    def years(self):
        start = datetime(self.start.year, 1, 1)
        if not hasattr(self, '_years'):
            self._years = rrule(YEARLY, dtstart=start, until=self.finish, cache=True)
        return self._years

    @property
    def months(self):
        start = datetime(self.start.year, self.start.month, 1)
        if not hasattr(self, '_months'):
            self._months = rrule(MONTHLY, dtstart=start, until=self.finish, cache=True)
        return self._months

    @property
    def days(self):
        start = datetime(self.start.year, self.start.month, self.start.day)
        if not hasattr(self, '_days'):
            self._days = rrule(DAILY, dtstart=start, until=self.finish, cache=True)
        return self._days

def year_view(request, *args, **kwargs):
    pass

def month_view(request, *args, **kwargs):
    pass

def day_view(request, *args, **kwargs):
    pass

def today_view(request, *args, **kwargs):
    pass

def occurrence_detail_redirect(request, year, month, day, slug, pk):
    return simple.redirect_to(
        request, reverse('occurrence-detail', args=(slug, pk)), permanent=True
    )

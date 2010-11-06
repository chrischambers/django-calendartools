from django.views.generic import simple
from django.core.urlresolvers import reverse
from django.utils.dates import MONTHS, MONTHS_3, WEEKDAYS, WEEKDAYS_ABBR

import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY

class SimpleProxy(object):
    def __init__(self, obj, *args, **kwargs):
        self._obj = obj
        super(SimpleProxy, self).__init__(*args, **kwargs)

    def __cmp__(self, other):
        return cmp(self._obj, other)

    def __add__(self, other):
        return self._obj + other

    def __sub__(self, other):
        return self._obj - other

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
            try:
                return getattr(self._obj, attr)
            except AttributeError, e:
                e = "%r and its Proxy(%r) have no '%s' attributes." % (
                    self._obj, self, attr
                )
                raise AttributeError, e


class DateTimeProxy(SimpleProxy):
    day_names = WEEKDAYS.values()
    day_names_abbr = WEEKDAYS_ABBR.values()
    month_names = MONTHS.values()
    month_names_abbr = MONTHS_3.values()

    def __init__(self, obj, *args, **kwargs):
        self._real_obj = obj
        obj = self.convert(obj)
        self.occurrences = kwargs.pop('occurrences', {})
        super(DateTimeProxy, self).__init__(obj, *args, **kwargs)
        self.process_occurrences()

    def process_occurrences(self):
        from django.db.models.query import QuerySet
        if not self.occurrences:
            return {}
        if isinstance(self.occurrences, QuerySet):
            data = {}
            for occ in self.occurrences:
                data[occ.start] = occ
            self.occurrences = data
            return
        self.occurrences = dict([(k, v) for (k, v) in self.occurrences.items() if k in self])
        return self.occurrences

    def convert(self, dt):
        """Returns naive datetime representation of date/datetime, with no
        microseconds."""
        for attr in ('hour', 'minute', 'second'):
            if not hasattr(dt, attr):
                return datetime(dt.year, dt.month, dt.day)
        return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    def interval(self):
        raise NotImplementedError

    def _coerce_to_datetime(self, dt):
        try:
            return self.convert(dt)
        except (AttributeError, ValueError, TypeError):
            return

    def __contains__(self, item):
        return self == item

    def __cmp__(self, other):
        other = self._coerce_to_datetime(other)
        if not other:
            return -1
        return cmp(self.start, other)

    def previous(self):
        return self.__class__(self._obj - self.interval)

    def next(self):
        return self.__class__(self._obj + self.interval)

    @property
    def start(self):
        return self._obj

    @property
    def finish(self):
        return (self.start + self.interval) - timedelta.resolution

class Hour(DateTimeProxy):
    interval = relativedelta(hours=+1)
    convert = lambda self, dt: datetime(dt.year, dt.month, dt.day, dt.hour)

    def __iter__(self):
        return (dt for dt in rrule(MINUTELY, dtstart=self.start, until=self.finish))

    @property
    def number(self):
        return self.hour


class Day(DateTimeProxy):
    interval = relativedelta(days=+1)
    convert = lambda self, dt: datetime(dt.year, dt.month, dt.day)

    def __iter__(self):
        return self.hours

    @property
    def name(self):
        return WEEKDAYS[self.weekday()]

    @property
    def abbr(self):
        return WEEKDAYS_ABBR[self.weekday()]

    @property
    def number(self):
        return self.day

    @property
    def hours(self):
        return (Hour(dt, occurrences=self.occurrences) for dt in
                rrule(HOURLY, dtstart=self.start, until=self.finish))


class Week(DateTimeProxy):
    interval = relativedelta(weeks=+1)
    convert = lambda self, dt: (datetime(dt.year, dt.month, dt.day) +
                          relativedelta(weekday=calendar.MONDAY, days=-6))

    def __iter__(self):
        return self.days

    @property
    def number(self):
        return ((self - datetime(self.year, 1, 1)).days / 7) + 1

    @property
    def days(self):
        return (Day(dt, occurrences=self.occurrences) for dt in rrule(DAILY,
            dtstart=self.start, until=self.finish
        ))


class Month(DateTimeProxy):
    interval = relativedelta(months=+1)
    convert = lambda self, dt: datetime(dt.year, dt.month, 1)

    def __iter__(self):
        return self.weeks

    @property
    def name(self):
        return MONTHS[self.month]

    @property
    def abbr(self):
        return MONTHS_3[self.month]

    @property
    def number(self):
        return self.month

    @property
    def weeks(self):
        return (Week(dt, occurrences=self.occurrences) for dt in rrule(WEEKLY,
            dtstart=self.start, until=self.finish
        ))

    @property
    def days(self):
        return (Day(dt, occurrences=self.occurrences) for dt in rrule(DAILY,
            dtstart=self.start, until=self.finish
        ))

    @property
    def calendar_display(self):
        cal = calendar.monthcalendar(self.year, self.month)
        return ((Day(datetime(self.year, self.month, num), occurrences=self.occurrences) if num else 0
                     for num in lst) for lst in cal)


class Year(DateTimeProxy):
    interval = relativedelta(years=+1)
    convert = lambda self, dt: datetime(dt.year, 1, 1)

    def __iter__(self):
        return self.months

    @property
    def number(self):
        return self.year

    @property
    def months(self):
        return (Month(dt, occurrences=self.occurrences) for dt in rrule(MONTHLY,
            dtstart=self.start, until=self.finish
        ))

    @property
    def days(self):
        for month in self.months:
            for dt in rrule(DAILY, dtstart=month.start, until=month.finish):
                yield Day(dt, occurrences=self.occurrences)
        # return ((Day(dt)
        #          for dt in rrule(DAILY, dtstart=month, utnil=month.finish))
        #          for month in self.months)


class Calendar(object):
    day_names = WEEKDAYS.values()
    day_names_abbr = WEEKDAYS_ABBR.values()
    month_names = MONTHS.values()
    month_names_abbr = MONTHS_3.values()


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
        return (Year(dt) for dt in self._years)

    @property
    def months(self):
        start = datetime(self.start.year, self.start.month, 1)
        if not hasattr(self, '_months'):
            self._months = rrule(MONTHLY, dtstart=start, until=self.finish, cache=True)
        return (Month(dt) for dt in self._months)

    @property
    def days(self):
        start = datetime(self.start.year, self.start.month, self.start.day)
        if not hasattr(self, '_days'):
            self._days = rrule(DAILY, dtstart=start, until=self.finish, cache=True)
        return self._days
        return (Day(dt) for dt in self._days)

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

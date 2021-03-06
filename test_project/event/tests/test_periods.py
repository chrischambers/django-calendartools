# -*- coding: UTF-8 -*-

import calendar
import pytz
from datetime import datetime, date, time, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, HOURLY, DAILY

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.dates import MONTHS, MONTHS_3, WEEKDAYS, WEEKDAYS_ABBR
from django.utils import translation

from django.test import TestCase
from nose.tools import *

from timezones.utils import adjust_datetime_to_timezone

from calendartools import defaults
from event.models import Calendar, Event, Occurrence
from calendartools.periods import (
    SimpleProxy, Period, Year, Month, Week, Day, Hour, TripleMonth,
    first_day_of_week
)
from calendartools.modelproxy import LocalizedOccurrenceProxy
from calendartools.validators.defaults.occurrence import (
    activate_default_occurrence_validators,
    deactivate_default_occurrence_validators
)


class TestSimpleProxy(TestCase):
    def setUp(self):
        self.datetime = datetime.now()
        self.proxy = SimpleProxy(self.datetime)

    def test_getattr(self):
        for prop in ('day', 'month', 'year'):
            assert_equal(getattr(self.proxy, prop), getattr(self.datetime, prop))
        proxy_strftime = getattr(self.proxy, 'strftime')
        real_strftime  = getattr(self.datetime, 'strftime')
        arg = '%Y/%m/%d'
        assert_equal(proxy_strftime(arg), real_strftime(arg))

        self.proxy.foo = 'foo'
        assert_equal(self.proxy.foo, 'foo')

    def test_comparisons(self):
        other_proxy = SimpleProxy(self.datetime)
        assert_equal(self.proxy, other_proxy)
        assert other_proxy >= self.proxy
        assert self.proxy <= other_proxy
        other_proxy = other_proxy + timedelta(1)
        assert other_proxy > self.proxy
        assert self.proxy < other_proxy
        other_proxy = other_proxy - timedelta(2)
        assert other_proxy < self.proxy
        assert self.proxy > other_proxy


class TestDateTimeProxies(TestCase):
    def setUp(self):
        translation.activate('en-gb')
        self.datetime = datetime(1982, 8, 17)
        self.year     = Year(self.datetime)
        self.month    = Month(self.datetime)
        self.week     = Week(self.datetime)
        self.day      = Day(self.datetime)
        self.hour     = Hour(datetime.combine(self.datetime.date(), time(6, 30, 5)))

    def tearDown(self):
        translation.deactivate()

    def test_default_datetimeproxy_conversion(self):
        mapping = (
            (date(1982, 8, 17), datetime(1982, 8, 17)),
            (datetime(1982, 8, 17, 6), datetime(1982, 8, 17, 6, 0, 0)),
            (datetime(1982, 8, 17, 6, 30), datetime(1982, 8, 17, 6, 30, 0)),
            (datetime(1982, 8, 17, 6, 30, 5), datetime(1982, 8, 17, 6, 30, 5)),
        )
        for inp, expected in mapping:
            assert_equal(Period(inp).start, expected)

    def test_hour_equality(self):
        equal = (
            datetime(1982, 8, 17, 6, 30, 5),
            datetime(1982, 8, 17, 6, 0, 0),
            datetime(1982, 8, 17, 7, 0, 0) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 17),
            datetime(1982, 8, 17, 6, 0, 0) - timedelta.resolution,
            datetime(1982, 8, 17, 7, 0, 0),
        )
        for dt in equal:
            assert_equal(self.hour, dt)
            assert self.hour >= dt
            assert self.hour <= dt
            assert dt in self.hour
        for dt in not_equal:
            assert_not_equal(self.hour, dt)
            assert_false(dt in self.hour)

    def test_day_equality(self):
        equal = (
            date(1982, 8, 17),
            datetime(1982, 8, 17),
            datetime(1982, 8, 17, 0, 0, 1),
            datetime(1982, 8, 17, 12, 30, 33),
            datetime(1982, 8, 18) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 16),
            date(1982, 8, 18),
            datetime(1982, 8, 16),
            datetime(1982, 8, 17) - timedelta.resolution,
            datetime(1982, 8, 18),
        )
        for dt in equal:
            assert_equal(self.day, dt)
            assert self.day >= dt
            assert self.day <= dt
            assert dt in self.day
        for dt in not_equal:
            assert_not_equal(self.day, dt)
            assert_false(dt in self.day)

    def test_week_equality(self):
        equal = (
            date(1982, 8, 16),
            date(1982, 8, 22),
            datetime(1982, 8, 16),
            datetime(1982, 8, 23) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 15),
            date(1982, 8, 23),
            datetime(1982, 8, 16) - timedelta.resolution,
            datetime(1982, 8, 23),
        )
        for dt in equal:
            assert_equal(self.week, dt)
            assert self.week >= dt
            assert self.week <= dt
            assert dt in self.week
        for dt in not_equal:
            assert_not_equal(self.week, dt)
            assert_false(dt in self.week)

    def test_month_equality(self):
        equal = (
            self.datetime.date(),
            date(1982, 8, 1),
            date(1982, 9, 1) - timedelta(1),
            self.datetime,
            datetime(1982, 8, 1),
            datetime(1982, 9, 1) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 1) - timedelta(1),
            date(1982, 9, 1),
            datetime(1982, 8, 1) - timedelta.resolution,
            datetime(1982, 9, 1),
        )
        for dt in equal:
            assert_equal(self.month, dt)
            assert self.month >= dt
            assert self.month <= dt
            assert dt in self.month
        for dt in not_equal:
            assert_not_equal(self.month, dt)
            assert_false(dt in self.month)

    def test_year_equality(self):
        equal = (
            date(1982, 1, 1),
            date(1982, 12, 31),
            datetime(1982, 1, 1),
            datetime(1983, 1, 1) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 1, 1) - timedelta(1),
            date(1982, 12, 31) + timedelta(1),
            datetime(1982, 1, 1) - timedelta.resolution,
            datetime(1983, 1, 1),
        )
        for dt in equal:
            assert_equal(self.year, dt)
            assert self.year >= dt
            assert self.year <= dt
            assert dt in self.year
        for dt in not_equal:
            assert_not_equal(self.year, dt)
            assert_false(dt in self.year)

    def test_membership(self):
        for i in (self.hour, self.day, self.week, self.month, self.year):
            assert i in self.year
        for i in (self.hour, self.day, self.week, self.month):
            assert i in self.month
        for i in (self.hour, self.day, self.week):
            assert i in self.week
        for i in (self.hour, self.day,):
            assert i in self.day
        for i in (self.hour,):
            assert i in self.hour


        class TenMinuteInterval(Period):
            interval = timedelta(minutes=10)
            def convert(self, dt):
                dt = super(TenMinuteInterval, self).convert(dt)
                return dt.replace(second=0)

        ten_min_period = TenMinuteInterval(datetime(1982, 8, 17, 6, 30, 5))
        good_inputs = (
            datetime(1982, 8, 17, 6, 30),
            datetime(1982, 8, 17, 6, 35),
            datetime(1982, 8, 17, 6, 40) - timedelta.resolution,
        )
        bad_inputs = (
            date(1982, 8, 17),
            datetime(1982, 8, 17, 6, 30) - timedelta.resolution,
            datetime(1982, 8, 17, 6, 40),
        )
        for inp in good_inputs:
            assert_in(inp, ten_min_period)
        for inp in bad_inputs:
            assert_not_in(inp, ten_min_period)

    def test_next(self):
        assert_equal(self.hour.next(),  datetime(1982, 8, 17, 7, 30, 5))
        assert_equal(self.day.next(),   datetime(1982, 8, 18))
        assert_equal(self.week.next(),  datetime(1982, 8, 24))
        assert_equal(self.month.next(), datetime(1982, 9, 17))
        assert_equal(self.year.next(),  datetime(1983, 8, 17))
        assert isinstance(self.hour.next(),  Hour)
        assert isinstance(self.day.next(),   Day)
        assert isinstance(self.week.next(),  Week)
        assert isinstance(self.month.next(), Month)
        assert isinstance(self.year.next(),  Year)

    def test_previous(self):
        assert_equal(self.hour.previous(),  datetime(1982, 8, 17, 5, 30, 5))
        assert_equal(self.day.previous(),   datetime(1982, 8, 16))
        assert_equal(self.week.previous(),  datetime(1982, 8, 10))
        assert_equal(self.month.previous(), datetime(1982, 7, 17))
        assert_equal(self.year.previous(),  datetime(1981, 8, 17))
        assert isinstance(self.hour.previous(),  Hour)
        assert isinstance(self.day.previous(),   Day)
        assert isinstance(self.week.previous(),  Week)
        assert isinstance(self.month.previous(), Month)
        assert isinstance(self.year.previous(),  Year)

    def test_day_hours_iteration(self):
        expected = list(rrule(HOURLY,
            dtstart=datetime(1982, 8, 17),
            until=datetime(1982, 8, 17, 23, 59, 59)
        ))
        actual = list(i for i in self.day.hours)
        assert_equal(expected, actual)
        assert all(isinstance(i, Hour) for i in actual)

    def test_week_days_iterator(self):
        start = datetime(1982, 8, 16) # monday
        expected = list(rrule(DAILY,
            dtstart=start,
            until=(start + timedelta(7)) - timedelta.resolution
        ))
        actual = list(i for i in self.week.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_month_weeks_iterator(self):
        expected = list(rrule(WEEKLY,
            dtstart=datetime(1982, 7, 26), # sunday
            until=datetime(1982, 8, 30)
        ))
        actual = list(i for i in self.month.weeks)
        assert_equal(expected, actual)
        assert all(isinstance(i, Week) for i in actual)

    def test_month_days_iterator(self):
        expected = list(rrule(DAILY,
            dtstart=datetime(1982, 8, 1),
            until=datetime(1982, 8, 31)
        ))
        actual = list(i for i in self.month.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_year_months_iterator(self):
        expected = list(rrule(MONTHLY,
            dtstart=datetime(1982, 1, 1),
            until=datetime(1982, 12, 31)
        ))
        actual = list(self.year.months)
        assert_equal(expected, actual)
        assert all(isinstance(i, Month) for i in actual)

    def test_year_days_iterator(self):
        expected = list(rrule(DAILY,
            dtstart=datetime(1982, 1, 1),
            until=datetime(1982, 12, 31)
        ))
        actual = list(self.year.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_day_iteration_returns_hours(self):
        assert_equal(list(self.day), list(self.day.hours))

    def test_week_iteration_returns_days(self):
        assert_equal(list(self.week), list(self.week.days))

    def test_month_iteration_returns_weeks(self):
        assert_equal(list(self.month), list(self.month.weeks))

    def test_year_iteration_returns_months(self):
        assert_equal(list(self.year), list(self.year.months))

    def test_names_property(self):
        dayname = calendar.day_name[self.datetime.weekday()]
        assert_equal(dayname, self.day.name)
        assert_equal('August', self.month.name)

    def test_abbr_property(self):
        abbr = calendar.day_abbr[self.datetime.weekday()]
        assert_equal(abbr, self.day.abbr)
        assert_equal('aug', self.month.abbr)

    def test_start_property(self):
        assert_equal(self.hour.start,  datetime(1982, 8, 17, 6))
        assert_equal(self.day.start,   datetime(1982, 8, 17))
        assert_equal(self.week.start,  datetime(1982, 8, 16))
        assert_equal(self.month.start, datetime(1982, 8, 1))
        assert_equal(self.year.start,  datetime(1982, 1, 1))

    def test_finish_property(self):
        smidge = timedelta.resolution
        assert_equal(self.hour.finish,  datetime(1982, 8, 17, 7) - smidge)
        assert_equal(self.day.finish,   datetime(1982, 8, 18) - smidge)
        assert_equal(self.week.finish,  datetime(1982, 8, 23) - smidge)
        assert_equal(self.month.finish, datetime(1982, 9, 1) - smidge)
        assert_equal(self.year.finish,  datetime(1983, 1, 1) - smidge)

    def test_number_property(self):
        assert_equal(self.hour.number,  6)
        assert_equal(self.day.number,   17)
        assert_equal(self.week.number,  self.datetime.isocalendar()[1])
        assert_equal(self.month.number, 8)
        assert_equal(self.year.number,  1982)

    def test_get_methods_for_more_general_periods(self):
        assert not hasattr(self.hour, 'get_hour')
        assert_equal(self.hour.get_day(), self.day)
        assert_equal(self.hour.get_week(), self.week)
        assert_equal(self.hour.get_month(), self.month)
        assert_equal(self.hour.get_year(), self.year)

        assert not hasattr(self.day, 'get_hour')
        assert not hasattr(self.day, 'get_day')
        assert_equal(self.day.get_week(), self.week)
        assert_equal(self.day.get_month(), self.month)
        assert_equal(self.day.get_year(), self.year)

        assert not hasattr(self.week, 'get_hour')
        assert not hasattr(self.week, 'get_day')
        assert not hasattr(self.week, 'get_week')
        assert_equal(self.week.get_month(), self.month)
        assert_equal(self.week.get_year(), self.year)

        assert not hasattr(self.month, 'get_hour')
        assert not hasattr(self.month, 'get_day')
        assert not hasattr(self.month, 'get_week')
        assert not hasattr(self.month, 'get_month')
        assert_equal(self.month.get_year(), self.year)

        assert not hasattr(self.year, 'get_hour')
        assert not hasattr(self.year, 'get_day')
        assert not hasattr(self.year, 'get_week')
        assert not hasattr(self.year, 'get_month')
        assert not hasattr(self.year, 'get_year')

    def test_month_calendar_display_property(self):
        expected = calendar.monthcalendar(self.datetime.year, self.datetime.month)
        actual = self.month.calendar_display
        actual = [[i.day if i else 0 for i in lst] for lst in actual]
        assert_equal(expected, actual)

    def test_intervals(self):
        intervals = self.day.intervals
        expected_start = datetime.combine(
            self.datetime.date(), defaults.TIMESLOT_START_TIME
        )
        expected_end = expected_start + defaults.TIMESLOT_END_TIME_DURATION
        assert_equal(intervals[0],  expected_start)
        assert_equal(intervals[-1], expected_end)

        expected_interval_count = 0
        while expected_start <= expected_end:
            expected_start += defaults.TIMESLOT_INTERVAL
            expected_interval_count += 1
        assert_equal(len(intervals), expected_interval_count)


class TestLocalization(TestCase):
    def setUp(self):
        self.datetime = datetime(1982, 8, 17)
        self.period   = Period(self.datetime)
        self.year     = Year(self.datetime)
        self.month    = Month(self.datetime)
        self.week     = Week(self.datetime)
        self.day      = Day(self.datetime)
        self.hour     = Hour(datetime.combine(self.datetime.date(), time(6, 30, 5)))
        self.original_language = settings.LANGUAGE_CODE

    def tearDown(self):
        translation.activate(self.original_language)

    def _test_localization(self, obj, mapping):
        for language, expected in mapping:
            translation.activate(language)
            assert_equal(unicode(obj), expected)

    def test_period_localization(self):
        mapping = (
            ('en', u'Aug. 17, 1982, midnight'),
            ('fr', u'17 août 1982 00:00:00'),
            ('de', u'17. August 1982 00:00:00'),
            ('zh-cn', u'八月 17, 1982, 午夜'),
        )
        self._test_localization(self.period, mapping)

    def test_year_localization(self):
        mapping = (
            ('en', u'Jan. 1, 1982'),
            ('fr', u'1 janvier 1982'),
            ('de', u'1. Januar 1982'),
            ('zh-cn', u'一月 1, 1982'),
        )
        self._test_localization(self.year, mapping)

    def test_month_localization(self):
        mapping = (
            ('en', u'Aug. 1, 1982'),
            ('fr', u'1 août 1982'),
            ('de', u'1. August 1982'),
            ('zh-cn', u'八月 1, 1982'),
        )
        self._test_localization(self.month, mapping)

    def test_week_localization(self):
        mapping = (
            ('en', u'Aug. 16, 1982'),
            ('fr', u'16 août 1982'),
            ('de', u'16. August 1982'),
            ('zh-cn', u'八月 16, 1982'),
        )
        self._test_localization(self.week, mapping)

    def test_day_localization(self):
        mapping = (
            ('en', u'Aug. 17, 1982'),
            ('fr', u'17 août 1982'),
            ('de', u'17. August 1982'),
            ('zh-cn', u'八月 17, 1982'),
        )
        self._test_localization(self.day, mapping)

    def test_hour_localization(self):
        mapping =  (
            ('en', u'midnight'),
            ('fr', u'00:00:00'),
            ('de', u'00:00:00'),
            ('zh-cn', u'午夜'),
        )
        self._test_localization(Hour(datetime(1982, 8, 17)), mapping)
        mapping = (
            ('en', u'6 a.m.'),
            ('fr', u'06:00:00'),
            ('de', u'06:00:00'),
            ('zh-cn', u'6 a.m.'),
        )
        self._test_localization(self.hour, mapping)


class TestDateAwareProperties(TestCase):
    def setUp(self):
        translation.activate('en-gb')
        self.now = datetime.now()
        self.periods = [Period, Year, Month, Week, Day, Hour]
        self.objects = [obj(self.now) for obj in self.periods]

    def tearDown(self):
        translation.deactivate()

    def test_day_names_property(self):
        for obj in self.objects:
            assert_equal(obj.day_names, WEEKDAYS.values())
            assert_equal(obj.day_names[0], 'Monday')
            assert_equal(obj.day_names[6], 'Sunday')

    def test_day_names_property_usa(self):
        translation.activate('en-us')
        objects = [obj(self.now) for obj in self.periods]
        for obj in objects:
            assert_equal(obj.day_names[0], 'Sunday')
            assert_equal(obj.day_names[6], 'Saturday')

    def test_day_names_abbr_property(self):
        for obj in self.objects:
            assert_equal(obj.day_names_abbr, WEEKDAYS_ABBR.values())
            assert_equal(obj.day_names_abbr[0], 'Mon')
            assert_equal(obj.day_names_abbr[6], 'Sun')

    def test_day_names_abbr_property_usa(self):
        translation.activate('en-us')
        objects = [obj(self.now) for obj in self.periods]
        for obj in objects:
            assert_equal(obj.day_names_abbr[0], 'Sun')
            assert_equal(obj.day_names_abbr[6], 'Sat')

    def test_month_names_property(self):
        for obj in self.objects:
            assert_equal(obj.month_names, MONTHS.values())
            assert_equal(obj.month_names[0], 'January')
            assert_equal(obj.month_names[11], 'December')

    def test_month_names_abbr_property(self):
        for obj in self.objects:
            assert_equal(obj.month_names_abbr, MONTHS_3.values())
            assert_equal(obj.month_names_abbr[0], 'jan')
            assert_equal(obj.month_names_abbr[11], 'dec')


class TestFirstDayOfWeek(TestCase):
    def setUp(self):
        translation.activate('en-gb')
        self.now = datetime.now()
        self.periods = [Period, Year, Month, Week, Day, Hour]
        self.objects = [obj(self.now) for obj in self.periods]

    def tearDown(self):
        translation.deactivate()

    def test_day_names_property(self):
        for obj in self.objects:
            assert_equal(obj.day_names[0], 'Monday')
            assert_equal(obj.day_names[6], 'Sunday')

    def test_day_names_property_usa(self):
        translation.activate('en-us')
        objects = [obj(self.now) for obj in self.periods]
        for obj in objects:
            assert_equal(obj.day_names[0], 'Sunday')
            assert_equal(obj.day_names[6], 'Saturday')

    def test_day_names_abbr_property(self):
        for obj in self.objects:
            assert_equal(obj.day_names_abbr[0], 'Mon')
            assert_equal(obj.day_names_abbr[6], 'Sun')

    def test_day_names_abbr_property_usa(self):
        translation.activate('en-us')
        objects = [obj(self.now) for obj in self.periods]
        for obj in objects:
            assert_equal(obj.day_names_abbr[0], 'Sun')
            assert_equal(obj.day_names_abbr[6], 'Sat')

    def test_week_properties(self):
        self.week = Week(datetime(1982, 8, 17))
        assert_equal(self.week.start, datetime(1982, 8, 16))
        assert_equal(self.week.finish, datetime(1982, 8, 23) - timedelta.resolution)

    def test_week_properties_usa(self):
        translation.activate('en-us')
        self.week = Week(datetime(1982, 8, 17))
        assert_equal(self.week.start, datetime(1982, 8, 15))
        assert_equal(self.week.finish, datetime(1982, 8, 22) - timedelta.resolution)


class TestTripleMonth(TestCase):
    def setUp(self):
        self.datetime = datetime(1982, 8, 17)
        self.trimonth = TripleMonth(self.datetime)
        self.expected = [
            datetime(1982, 8, 1), datetime(1982, 9, 1), datetime(1982, 10, 1)
        ]

    def test_start_and_finish(self):
        assert_equal(self.trimonth.start, self.expected[0])
        assert_equal(self.trimonth.finish, datetime(1982, 11, 1)
                     - timedelta.resolution)

    def test_iterates_over_months(self):
        actual = [i for i in self.trimonth]
        assert_equal(self.expected, actual)

    def test_first_month_property(self):
        assert_equal(self.trimonth.first_month, self.expected[0])

    def test_second_month_property(self):
        assert_equal(self.trimonth.second_month, self.expected[1])

    def test_third_month_property(self):
        assert_equal(self.trimonth.third_month, self.expected[2])


class TestWeek(TestCase):
    def setUp(self):
        translation.activate('en-gb')
        self.datetime = datetime(1982, 8, 17)   # Tuesday
        self.week = Week(self.datetime)
        self.expected = [
            datetime(1982, 8, 16),              # Monday
            datetime(1982, 8, 22)
        ]

    def tearDown(self):
        translation.deactivate()

    def test_first_day_of_week(self):
        assert_equal(first_day_of_week(self.datetime), self.expected[0])

    def test_first_day(self):
        assert_equal(self.week.first_day, self.expected[0])

    def test_last_day(self):
        assert_equal(self.week.last_day, self.expected[1])

    def test_first_day_of_week_usa(self):
        translation.activate('en-us')
        self.week = Week(self.datetime)
        assert_equal(first_day_of_week(self.datetime),
                    self.expected[0] - timedelta(1))

    def test_first_day_usa(self):
        translation.activate('en-us')
        self.week = Week(self.datetime)
        assert_equal(self.week.first_day, self.expected[0] - timedelta(1))

    def test_last_day_usa(self):
        translation.activate('en-us')
        self.week = Week(self.datetime)
        assert_equal(self.week.last_day, self.expected[1] - timedelta(1))


class TestDateTimeProxiesWithOccurrences(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.start = datetime.now() + timedelta(1)
        Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(hours=2)
        )
        Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            status=Occurrence.STATUS.cancelled,
            finish=self.start + timedelta(hours=2)
        )

        self.year = Year(self.start, occurrences=Occurrence.objects.all())

    def test_occurrences_populated(self):
        for month in self.year.months:
            if month != self.start:
                assert not month.occurrences
            else:
                assert_equal(len(month.occurrences), 2)
                for day in month.days:
                    if day != self.start:
                        assert not day.occurrences
                    else:
                        assert_equal(len(day.occurrences), 2)
                        for hour in day.hours:
                            if hour != self.start:
                                assert not hour.occurrences
                            else:
                                assert_equal(len(hour.occurrences), 2)

    def test_occurrences_localized_correctly(self):
        timezone = 'Antarctica/McMurdo'
        occurrences = Occurrence.objects.all()
        localized_year = Year(
            self.start, occurrences=occurrences, timezone=timezone
        )
        assert_equal(localized_year.timezone, pytz.timezone(timezone))
        assert self.year.timezone is None

        for o in localized_year.occurrences:
            assert isinstance(o, LocalizedOccurrenceProxy)
        for localized_month, month in zip(localized_year, self.year):
            for localized_o, o in zip(localized_month.occurrences, occurrences):
                assert_equal(localized_o.real_start, o.start.replace(tzinfo=None))
                assert_equal(localized_o.real_finish, o.finish.replace(tzinfo=None))
                for attr in ('start', 'finish'):
                    expected = adjust_datetime_to_timezone(
                        getattr(o, attr), settings.TIME_ZONE, timezone
                    )
                    assert_equal(getattr(localized_o, attr), expected)


class TestDateTimeProxiesWithLocalizedOccurrences(TestCase):
    def setUp(self):
        deactivate_default_occurrence_validators()
        translation.activate('en-gb')
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.start = datetime(1982, 8, 16)
        self.end_of_week = self.start + timedelta(7) - timedelta.resolution

        mapping = [
            (self.start, self.start + timedelta(hours=2)),
            (self.end_of_week, self.end_of_week + timedelta(hours=2)),
        ]
        for start, finish in mapping:
            Occurrence.objects.create(
                calendar=self.calendar,
                event=self.event,
                start=start,
                finish=finish
            )
        self.week = Week(self.start, occurrences=Occurrence.objects.all())

    def tearDown(self):
        activate_default_occurrence_validators()
        translation.activate('en-us')

    def test_membership(self):
        assert_equal(len(self.week.occurrences), 2)

    def test_localization(self):
        occurrences = Occurrence.objects.all()
        timezones = [
            'Antarctica/McMurdo', # GMT + 1300
            'Pacific/Midway',     # GMT - 1100
        ]

        for timezone in timezones:
            localized_week = Week(
                self.start, occurrences=occurrences, timezone=timezone
            )
            assert_equal(len(localized_week.occurrences), 1)


class TestWeeksAttribute(TestCase):
    def setUp(self):
        translation.activate('en-gb')
        self.month = Month(date(2011, 1, 1))       # Saturday

    def tearDown(self):
        translation.deactivate()

    def test_weeks_attribute(self):
        expected = [
            date(2010, 12, 27),                    # All Mondays
            date(2011, 1,  3),
            date(2011, 1,  10),
            date(2011, 1,  17),
            date(2011, 1,  24),
            date(2011, 1,  31),
        ]
        expected = [Week(dt) for dt in expected]
        assert_equal(self.month.weeks, expected)

        self.month = Month(date(2011, 2, 1))       # Tuesday
        expected = [
            date(2011, 1,  31),
            date(2011, 2,  7),
            date(2011, 2,  14),
            date(2011, 2,  21),
            date(2011, 2,  28)
        ]
        expected = [Week(dt) for dt in expected]
        assert_equal(self.month.weeks, expected)

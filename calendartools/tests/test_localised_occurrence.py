import pytz
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User

from django.test import TestCase
from nose.tools import *


from timezones.utils import localtime_for_timezone
from calendartools.tests.event.models import Calendar, Event, Occurrence
from calendartools.periods.localised_occurrence_proxy import (
    LocalizedOccurrenceProxy
)
from calendartools.validators.defaults.occurrence import (
    activate_default_occurrence_validators,
    deactivate_default_occurrence_validators
)

class TestLocalisedOccurrenceProxy(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)
        self.occurrence = self.event.add_occurrences(
            self.calendar, self.start, self.finish)[0]
        self.timezone = 'America/Chicago'
        self.localised = LocalizedOccurrenceProxy(
            self.occurrence, timezone=self.timezone
        )
        deactivate_default_occurrence_validators()

    def tearDown(self):
        activate_default_occurrence_validators()

    def test_default_timezone(self):
        original_timezone = settings.TIME_ZONE
        try:
            settings.TIME_ZONE = 'UTC'
            expected = pytz.timezone('UTC')
            settings.TIME_ZONE = self.timezone
            expected = pytz.timezone(self.timezone)
            assert_equal(self.localised.default_timezone, expected)
        finally:
            settings.TIME_ZONE = original_timezone

    def test_real_start_property_populated(self):
        assert hasattr(self.localised, 'real_start')
        assert_equal(self.localised.real_start, self.occurrence.start)

    def test_real_finish_property_populated(self):
        assert hasattr(self.localised, 'real_finish')
        assert_equal(self.localised.real_finish, self.occurrence.finish)

    def test_start_property_localised_to_specified_timezone(self):
        expected = localtime_for_timezone(self.start, self.timezone)
        assert_equal(self.localised.start, expected)

    def test_finish_property_localised_to_specified_timezone(self):
        expected = localtime_for_timezone(self.finish, self.timezone)
        assert_equal(self.localised.finish, expected)

    def test_assign_new_datetime_to_start_property_updates_real_start(self):
        new_date = self.start + timedelta(days=5)
        dts = [
            localtime_for_timezone(new_date, 'UTC'),
            localtime_for_timezone(new_date, 'America/Chicago'),
            localtime_for_timezone(new_date, 'Asia/Shanghai'),
            localtime_for_timezone(new_date, 'Europe/London'),
            localtime_for_timezone(new_date, 'Australia/Sydney'),
        ]
        expected = new_date
        for dt in dts:
            self.localised.start = dt
            assert_equal(self.localised.real_start, expected)
            self.localised.save()
            occurrence = Occurrence.objects.get(pk=self.occurrence.pk)
            assert_equal(occurrence.start, expected)

    def test_assign_new_datetime_to_finish_property_updates_real_finish(self):
        new_date = self.finish + timedelta(days=5)
        dts = [
            localtime_for_timezone(new_date, 'UTC'),
            localtime_for_timezone(new_date, 'America/Chicago'),
            localtime_for_timezone(new_date, 'Asia/Shanghai'),
            localtime_for_timezone(new_date, 'Europe/London'),
            localtime_for_timezone(new_date, 'Australia/Sydney'),
        ]
        expected = new_date
        for dt in dts:
            self.localised.finish = dt
            assert_equal(self.localised.real_finish, expected)
            self.localised.save()
            occurrence = Occurrence.objects.get(pk=self.occurrence.pk)
            assert_equal(occurrence.finish, expected)

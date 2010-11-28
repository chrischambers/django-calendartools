import pytz
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User

from django.test import TestCase
from nose.tools import *

from timezones.utils import localtime_for_timezone, adjust_datetime_to_timezone
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

    def test_timezone_property(self):
        expected = pytz.timezone('America/Chicago')
        assert_equal(self.localised.timezone, expected)

        # Should handle actual timezone object as well as string name:
        localised2 = LocalizedOccurrenceProxy(
            self.occurrence, timezone=expected
        )
        assert_equal(localised2.timezone, expected)

        # Garbage input results in a timezone of None:
        localised3 = LocalizedOccurrenceProxy(
            self.occurrence, timezone='Non-Existent Timezone'
        )
        assert localised3.timezone is None

    def test_default_timezone_property(self):
        original_timezone = settings.TIME_ZONE
        try:
            settings.TIME_ZONE = 'UTC'
            expected = pytz.timezone('UTC')
            settings.TIME_ZONE = self.timezone
            expected = pytz.timezone(self.timezone)
            assert_equal(self.localised.default_timezone, expected)
        finally:
            settings.TIME_ZONE = original_timezone

    def test_localised_occurrence_proxy_wrapping_proxy_works_properly(self):
        timezone = 'Antarctica/McMurdo'
        localised = LocalizedOccurrenceProxy(
            self.localised, timezone=timezone
        )
        assert_equal(localised.real_start, self.occurrence.start)
        assert_equal(localised.real_finish, self.occurrence.finish)
        for attr in ('start', 'finish'):
            expected = adjust_datetime_to_timezone(
                getattr(self.occurrence, attr),
                settings.TIME_ZONE,
                timezone
            )
            assert_equal(getattr(localised, attr), expected)

    def test_real_datetime_property_populated(self):
        assert hasattr(self.localised, 'real_start')
        assert hasattr(self.localised, 'real_finish')
        assert_equal(self.localised.real_start, self.occurrence.start)
        assert_equal(self.localised.real_finish, self.occurrence.finish)

    def test_datetime_properties_localised_to_specified_timezone(self):
        expected = localtime_for_timezone(self.start, self.timezone)
        assert_equal(self.localised.start, expected)
        expected = localtime_for_timezone(self.finish, self.timezone)
        assert_equal(self.localised.finish, expected)

    def test_assign_to_datetime_properties_updates_real_datetime_properties(self):
        new_date = self.start + timedelta(days=5)
        dts = [
            localtime_for_timezone(new_date, 'UTC'),
            localtime_for_timezone(new_date, 'America/Chicago'),
            localtime_for_timezone(new_date, 'Asia/Shanghai'),
            localtime_for_timezone(new_date, 'Europe/London'),
            localtime_for_timezone(new_date, 'Australia/Sydney'),
        ]
        expected = new_date
        for attr in ('start', 'finish'):
            for dt in dts:
                setattr(self.localised, attr, dt)
                assert_equal(getattr(self.localised, 'real_%s' % attr), expected)
                self.localised.save()
                occurrence = Occurrence.objects.get(pk=self.occurrence.pk)
                assert_equal(getattr(occurrence, attr), expected)

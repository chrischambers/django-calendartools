from datetime import datetime, date, timedelta
from dateutil import rrule

from django import forms
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase

from nose.tools import *

from calendartools import constants, defaults, signals
from calendartools.tests.event.models import (
    Calendar, Event, Occurrence, Attendance
)
from calendartools.forms import MultipleOccurrenceForm, AttendanceForm
from calendartools.validators import BaseValidator
from calendartools.validators.defaults.attendance import (
    CannotAttendFutureEventsValidator
)


class TestAttendanceForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        self.start = datetime.now() + timedelta(1)
        self.occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(1)
        )

    def test_unpersisted_instance_saved_for_valid_forms(self):
        attendance = Attendance(user=self.user, occurrence=self.occurrence)
        assert not attendance.pk
        form = AttendanceForm(instance=attendance, data={})
        assert form.is_valid()
        attendance = form.save()
        assert attendance.pk

    def test_clean_method_sets_instance_cancelled_when_status_is_booked(self):
        attendance = Attendance.objects.create(
            user=self.user,
            occurrence=self.occurrence,
        )
        form = AttendanceForm(instance=attendance, data={})
        assert form.instance.status == Attendance.BOOKED
        assert form.is_valid()
        assert form.instance.status == Attendance.CANCELLED

    def test_clean_method_performs_noop_if_status_attended(self):
        try:
            signals.collect_validators.disconnect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )
            attendance = Attendance.objects.create(
                user=self.user,
                occurrence=self.occurrence,
                status=Attendance.ATTENDED
            )
            form = AttendanceForm(instance=attendance, data={})
            assert form.is_valid()
            form.save()
            assert form.instance.status == Attendance.ATTENDED
        finally:
            signals.collect_validators.connect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )


class TestMultipleOccurrenceFormValidation(TestCase):
    def setUp(self):
        # For readable tests:
        self.weekday_long = {}
        for val, key in constants.WEEKDAY_LONG:
            # call method to force proxy evaluation:
            self.weekday_long[key.title()] = val

        self.creator = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.today = date.today()
        self.tomorrow = self.today + timedelta(1)

        self.full_data = {
            'calendar':               self.calendar.pk,
            'day':                    self.tomorrow,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            # Repetitions - a given count:
            'repeats':                'count',
            'count':                  '1',

            # Repetitions - until specified date:
            'repeats':                'until',
            'until':                  self.tomorrow + timedelta(3),

            # Frequency + Variations:
            # Variant 1: Daily
            'freq':                   rrule.DAILY,
            'interval':               6, # days

            # Variant 2: Weekly
            'freq':                   rrule.WEEKLY,
            'week_days':              [self.weekday_long['Tuesday']],

            # Variant 3.1: Monthly, Ordinal
            'freq':                   rrule.MONTHLY,
            'month_option':           'on',
            'month_ordinal':          '1',
            'month_ordinal_day':      self.weekday_long['Tuesday'],

            # Variant 3.2: Monthly, Each
            'freq':                   rrule.MONTHLY,
            'month_option':           'each',
            'each_month_day':         [1,3,5],

            # Variant 3.1: Yearly, Months
            'freq':                   rrule.YEARLY,
            'is_year_month_ordinal':  False,
            'year_months':            [1,12],

            # Variant 3.2: Yearly, Ordinal
            'freq':                   rrule.YEARLY,
            'is_year_month_ordinal':  True,
            'year_month_ordinal':     '1',
            'year_month_ordinal_day': self.weekday_long['Tuesday'],
        }

        self.data = {
            'calendar':               self.calendar.pk,
            'day':                    self.tomorrow,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',
            'repeats':                'count',
            'count':                  7,
            'interval':               1, # days
        }
        self.maximum = defaults.MAX_OCCURRENCE_CREATION_COUNT

    def test_with_good_inputs(self):
        form = MultipleOccurrenceForm(event=self.event, data=self.full_data)
        assert form.is_valid(), form.errors.as_text()
        form.save()

    def test_initial_dtstart(self):
        pass

    def test_build_rrule_params(self):
        pass

    def _test_formfield(self, formfield, invalid_inputs, valid_inputs):
        """Utility method: encapsulates all the 'meat' of the test to reduce
        verbosity. Make sure ``self.data`` is in the right state before running
        this."""
        form = MultipleOccurrenceForm(event=self.event, data=self.data)
        assert not form.is_valid(), (
            "form with no %s key valid when it should not be." % formfield
        )
        for i in invalid_inputs:
            self.data[formfield] = i
            form = MultipleOccurrenceForm(event=self.event, data=self.data)
            assert not form.is_valid(), (
                "Invalid %s value %s identified as valid." % (formfield, i)
            )
        for i in valid_inputs:
            self.data[formfield] = i
            form = MultipleOccurrenceForm(event=self.event, data=self.data)
            assert form.is_valid(), form.errors.as_text()

    def test_calendar_required(self):
        self.data.update({'freq': rrule.DAILY})
        del self.data['calendar']
        form = MultipleOccurrenceForm(event=self.event, data=self.data)
        assert not form.is_valid()
        assert "This field is required." in form.errors.get('calendar', [])

    def test_repeats_method_count_must_have_count_gt_1(self):
        """If repeats method == 'count', 'count' parameter
        must be provided, and its value must be gt 1."""
        invalid_inputs = [None, -2, -1, 0, self.maximum]
        valid_inputs   = [1, 10, 20, 30, self.maximum - 1]
        self.data.update({'freq': rrule.DAILY })
        del self.data['count']
        self._test_formfield('count', invalid_inputs, valid_inputs)

    def test_repeats_method_until_must_have_datetime_gt_start(self):
        """If repeats method == 'until', 'until' parameter
        must be provided, and its value must be a date greater than the start
        date provided."""
        invalid_inputs = (
            None,
            date.today(),
            date.today() - timedelta(1),
            self.tomorrow,
        )
        valid_inputs = (
            self.tomorrow + timedelta(1),
            self.tomorrow + timedelta(2),
            self.tomorrow + timedelta(10),
            self.tomorrow + timedelta(100),
        )

        self.data.update({
            'repeats':                'until',
            'freq':                   rrule.WEEKLY,
            'week_days':              [self.weekday_long['Tuesday']],
        })
        self._test_formfield('until', invalid_inputs, valid_inputs)

    def test_until_gt_start_only_applies_when_repeat_method_until(self):
        invalid_inputs = (
            None,
            date.today(),
            date.today() - timedelta(1),
            self.tomorrow,
        )
        self.data.update({
            'repeats':                'count',
            'freq':                   rrule.DAILY,
        })
        for i in invalid_inputs:
            self.data['until'] = i
            form = MultipleOccurrenceForm(event=self.event, data=self.data)
            assert form.is_valid(), form.errors.as_text()

    def test_interval(self):
        invalid_inputs = [None, 0, -1, 1000, self.maximum]
        valid_inputs   = [1,2,3,4,5,10,20,50, self.maximum - 1]
        self.data['freq'] = rrule.DAILY
        del self.data['interval']
        self._test_formfield('interval', invalid_inputs, valid_inputs)

    def test_weekly_freq_requires_week_days(self):
        invalid_inputs = [None, [None], [], [0], [8], [0,1,2], [6,7,8]]
        valid_inputs = (
            [[i] for i in self.weekday_long.values()] +
            [[1,7], [1,2,3,4,5,6,7], [6,7], [1,2]]
        )
        self.data['freq'] = rrule.WEEKLY
        self._test_formfield('week_days', invalid_inputs, valid_inputs)

    def test_monthly_freq_requires_month_option(self):
        invalid_inputs = [None, '', 'something', 'odd']
        valid_inputs   = ['on', 'each']
        self.data.update({
            'freq':                   rrule.MONTHLY,
            'month_ordinal':          '1',
            'month_ordinal_day':      self.weekday_long['Tuesday'],
            'each_month_day':         [1,3,5],
        })
        self._test_formfield('month_option', invalid_inputs, valid_inputs)

    def test_monthly_freq_option_on_requires_ordinal(self):
        invalid_inputs = [None, 0]
        valid_inputs   = [1,2,3,4,-1]
        self.data.update({
            'freq':                   rrule.MONTHLY,
            'month_option':           'on',
            'month_ordinal_day':      self.weekday_long['Tuesday'],
        })
        self._test_formfield('month_ordinal', invalid_inputs, valid_inputs)

    def test_monthly_freq_option_on_requires_ordinal_day(self):
        invalid_inputs = [None, 0]
        valid_inputs   = self.weekday_long.values()
        self.data.update({
            'freq':                   rrule.MONTHLY,
            'month_option':           'on',
            'month_ordinal':          1,
        })
        self._test_formfield('month_ordinal_day', invalid_inputs, valid_inputs)

    def test_monthly_freq_option_each_requires_each_month_day(self):
        invalid_inputs = (
            None, [None], [], [0], [32], [100],
            [0,1,2], [1,2,32],
        )
        valid_inputs = (
            [1], [2], [10], [20], [28], [29], [30], [31],
            [1,2], [1,2,10], [1,2,10,20], [1,2,10,20,30], [1,2,10,20,30,31],
        )
        self.data.update({
            'freq':                   rrule.MONTHLY,
            'month_option':           'each',
        })
        self._test_formfield('each_month_day', invalid_inputs, valid_inputs)

    def test_is_year_month_ordinal(self):
        """Should always be in cleaned data, and always equal bool(input)"""
        falsey_inputs = ['', None, False, []]
        truthy_inputs = [True, 1, '1', 'foo']
        self.data.update({
            'freq':                   rrule.YEARLY,
            'year_months':            [1,12],
            'year_month_ordinal':     '1',
            'year_month_ordinal_day': self.weekday_long['Tuesday'],
        })
        form = MultipleOccurrenceForm(event=self.event, data=self.data)
        assert form.is_valid(), form.errors.as_text()
        assert not form.cleaned_data['is_year_month_ordinal']

        for i in falsey_inputs:
            self.data['is_year_month_ordinal'] = i
            form = MultipleOccurrenceForm(event=self.event, data=self.data)
            assert form.is_valid(), form.errors.as_text()
            assert not form.cleaned_data['is_year_month_ordinal']
        for i in truthy_inputs:
            self.data['is_year_month_ordinal'] = i
            form = MultipleOccurrenceForm(event=self.event, data=self.data)
            assert form.is_valid(), form.errors.as_text()
            assert form.cleaned_data['is_year_month_ordinal']

    def test_yearly_freq_ord_true_requires_ordinal(self):
        invalid_inputs = [None, 0]
        valid_inputs   = [1,2,3,4,-1]
        self.data.update({
            'freq':                   rrule.YEARLY,
            'is_year_month_ordinal':  True,
            'year_month_ordinal_day': self.weekday_long['Tuesday'],
        })
        self._test_formfield('year_month_ordinal', invalid_inputs, valid_inputs)

    def test_yearly_freq_ord_true_requires_ordinal_day(self):
        invalid_inputs = [None, 0]
        valid_inputs   = self.weekday_long.values()
        self.data.update({
            'freq':                   rrule.YEARLY,
            'is_year_month_ordinal':  True,
            'year_month_ordinal':     '1',
        })
        self._test_formfield('year_month_ordinal_day', invalid_inputs, valid_inputs)

    def test_yearly_freq_ord_false_requires_year_months(self):
        invalid_inputs = (
            None, [None], [0], [13], [20], [0,1,2], [10,11,12,13]
        )
        valid_inputs = (
            [[i] for i in range(1,13)] +
            [[1,2], [11,12], [1,2,3,4,5,6], [7,8,9,10,11,12]]
        )
        first_day_of_next_month = self.today.replace(
            month=self.today.month+1, day=1
        )
        # Necessary because of potential slow-down: see test below.
        self.data.update({
            'day':                    first_day_of_next_month,
            'freq':                   rrule.YEARLY,
            'is_year_month_ordinal':  False,
        })
        self._test_formfield('year_months', invalid_inputs, valid_inputs)

    def test_rrule_delay(self):
        # The current implementation of rrule.rrule has a very long delay when
        # you evaluate the (empty) iterable returned when you create
        # occurrences on, say, every 31st of September of 30th of February
        # (i.e. non-existent days):
        last_day_of_month = date(2010, 10, 31)
        rrule_params = {'count': 7, 'bymonth': [6], 'freq': 0, 'interval': 1}
        iterable = rrule.rrule(dtstart=last_day_of_month, **rrule_params)
        # list(iterable)

        # The interesting thing is, however, that this delay doesn't apply when
        # at least one of the months specified *does* have actual occurrences
        # in it (even if all the other months would generate non-existent
        # days):
        rrule_params = {'count': 7, 'bymonth': [12,6], 'freq': 0, 'interval': 1}
        iterable = rrule.rrule(dtstart=last_day_of_month, **rrule_params)
        # list(iterable)

        # One possible workaround:
        # - Determine days in month(s)
        # - if relevant_datetime.days > days in min(months(s)):
        # - handle (probably by removing that month from the bymonth list)


class TestMultipleOccurrenceFormModelValidation(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.add_occurrence_perm = Permission.objects.get(
            content_type__app_label=defaults.CALENDAR_APP_LABEL,
            codename='add_occurrence'
        )
        self.user.user_permissions.add(self.add_occurrence_perm)
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        self.today = date.today()
        self.tomorrow = self.today + timedelta(1)


        class TomorrowEventsNotAllowed(BaseValidator):
            error_message = "Events can't start tomorrow!"
            def validate(self):
                tomorrow = date.today() + timedelta(1)
                if self.instance.start.date() == tomorrow:
                    raise forms.ValidationError(self.error_message)

        self.validator = TomorrowEventsNotAllowed
        signals.collect_validators.connect(self.validator, sender=Occurrence)
        self.data = {
            '_add':                   True,
            'calendar':               self.calendar.pk,
            'day':                    self.tomorrow,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',
            'repeats':                'count',
            'count':                  2,
            'interval':               1, # days
            'freq':                   rrule.DAILY,
        }
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def tearDown(self):
        signals.collect_validators.disconnect(self.validator, sender=Occurrence)

    def test_model_form_validation_occurs(self):
        form = MultipleOccurrenceForm(event=self.event, data=self.data)
        assert form.is_valid(), form.errors.as_text()
        assert_equal(len(form.valid_occurrences), 1)
        assert_equal(len(form.invalid_occurrences), 1)
        assert_equal(len(form.occurrences), 2)
        assert_equal(form.invalid_occurrences[0][1], self.validator.error_message)

    def test_redirect_to_confirm_occurrences_if_invalid_occurrences(self):
        response = self.client.post(
            reverse('event-detail', args=[self.event.slug]),
            data=self.data, follow=True
        )
        self.assertRedirects(response, reverse('confirm-occurrences'))


    # Mis-matched groups shouldn't validate?

    # Combination where ordinal AND ordinal_day not provided?

    # Ensure that the right objects are created when BOTH variant .n's are
    # provided.

    # Test groups: atm, Frequencies are EITHER 1,2,3,4 - but that's only
    # because of the widget. What happens when multiple options are available?

    # How are duplicate 'each_month_day' values handled? Introduce clean_field
    # method which tries to coerce to set?

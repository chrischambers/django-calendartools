from datetime import date, timedelta
from dateutil import rrule
from django.contrib.auth.models import User
from django.test import TestCase
from nose.tools import *
from calendartools import constants
from calendartools.models import Event
from calendartools.forms import MultipleOccurrenceForm

class TestMultipleOccurrenceForm(TestCase):
    def setUp(self):
        # For readable tests:
        self.weekday_long = {}
        for val, key in constants.WEEKDAY_LONG:
            self.weekday_long[key.title()] = val

        self.creator = User.objects.create(username='TestyMcTesterson')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        today = date.today()
        self.tomorrow = today + timedelta(1)
        self.tomorrow_str = self.tomorrow.strftime('%Y-%m-%d')
        self.data = {
            'day':                    self.tomorrow_str,
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

    def test_with_good_inputs(self):
        form = MultipleOccurrenceForm(self.data)
        assert form.is_valid(), form.errors.as_text()
        form.save(self.event)

    def test_initial_dtstart(self):
        pass

    def test_build_rrule_params(self):
        pass

    def test_repeats_method_count_must_have_count_gt_1(self):
        """If repeats method == 'count', 'count' parameter
        must be provided, and its value must be gt 1."""
        invalid_inputs = [None, -2, -1, 0, 1000]
        valid_inputs = [1, 10, 20, 50, 100, 500, 999]
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',

            'freq':                   rrule.DAILY,
            'interval':               1, # days
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with repeats=count and no count key valid."
        )
        for i in invalid_inputs:
            data['count'] = i
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid count value %s identified as valid" % i
            )
        for i in valid_inputs:
            data['count'] = i
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_repeats_method_until_must_have_datetime_gt_now(self):
        """If repeats method == 'until', 'until' parameter
        must be provided, and its value must be a date greater than now."""
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

        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'until',

            'freq':                   rrule.WEEKLY,
            'week_days':              [self.weekday_long['Tuesday']],
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with repeats=until and no until key valid."
        )
        for i in invalid_inputs:
            data['until'] = i
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid until value %s identified as valid" % i
            )
        for i in valid_inputs:
            data['until'] = i
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_daily_freq_requires_interval_gt_1(self):
        invalid_intervals = [None, 0, -1, 1000]
        valid_intervals = [1,2,3,4,5,10,20,50,100,500,999]
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.DAILY,
        }

        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=DAILY and no interval key valid."
        )
        for i in invalid_intervals:
            data['interval'] = i
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "form with freq=DAILY and interval == %s valid." % i
            )
        for i in valid_intervals:
            data['interval'] = i
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_weekly_freq_requires_week_days(self):
        valid_inputs = (
            [[i] for i in self.weekday_long.values()] +
            [[1,7], [1,2,3,4,5,6,7], [6,7], [1,2]]
        )
        invalid_inputs = [None, [None], [], [0], [8], [0,1,2], [6,7,8]]

        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.WEEKLY,
        }

        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=WEEKLY and no week_days key valid."
        )
        for i in invalid_inputs:
            data['week_days'] = i
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid week_days value %s identified as valid" % i
            )
        for i in valid_inputs:
            data['week_days'] = i
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_monthly_freq_requires_month_option(self):
        invalid_inputs = [None, '', 'something', 'odd']
        valid_inputs = ['on', 'each']
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.MONTHLY,

            'month_ordinal':          '1',
            'month_ordinal_day':      self.weekday_long['Tuesday'],
            'each_month_day':         [1,3,5],
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=MONTHLY and no month_options key valid."
        )
        for i in invalid_inputs:
            data['month_option'] = i
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid month_options value %s identified as valid" % i
            )
        for i in valid_inputs:
            data['month_option'] = i
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_monthly_freq_option_on_requires_ordinal(self):
        invalid_ordinals = [None, 0]
        valid_ordinals = [1,2,3,4,-1]
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.MONTHLY,

            'month_option':           'on',
            'month_ordinal_day':      self.weekday_long['Tuesday'],
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=MONTHLY, month_options=on and no month_ordinal "
            "key valid."
        )
        for o in invalid_ordinals:
            data['month_ordinal'] = o
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid month_ordinal value %s identified as valid" % o
            )
        for o in valid_ordinals:
            data['month_ordinal'] = o
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_monthly_freq_option_on_requires_ordinal_day(self):
        invalid_ordinal_days = [None, 0]
        valid_ordinal_days = self.weekday_long.values()
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.MONTHLY,

            'month_option':           'on',
            'month_ordinal':          1,
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=MONTHLY, month_options=on and no "
            "month_ordinal_day key valid."
        )
        for d in invalid_ordinal_days:
            data['month_ordinal_day'] = d
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid month_ordinal_day value %s identified as valid" % o
            )
        for d in valid_ordinal_days:
            data['month_ordinal_day'] = d
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_monthly_freq_option_each_requires_each_month_day(self):
        valid_month_days = (
            [1], [2], [10], [20], [28], [29], [30], [31],
            [1,2], [1,2,10], [1,2,10,20], [1,2,10,20,30], [1,2,10,20,30,31],
        )
        invalid_month_days = (
            None, [None], [], [0], [32], [100],
            [0,1,2], [1,2,32],
        )
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.MONTHLY,

            'month_option':           'each',
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=MONTHLY, month_options=each and no "
            "each_month_day key valid."
        )
        for d in invalid_month_days:
            data['each_month_day'] = d
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid each_month_day value %s identified as valid" % d
            )
        for d in valid_month_days:
            data['each_month_day'] = d
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_yearly_freq_requires_is_year_month_ordinal(self):
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.YEARLY,

            'year_months':            [1,12],
            'year_month_ordinal':     '1',
            'year_month_ordinal_day': self.weekday_long['Tuesday'],
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=YEARLY and no is_year_month_ordinal key valid."
        )
        data['is_year_month_ordinal'] = None
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=YEARLY and is_year_month_ordinal == None valid."
        )
        data['is_year_month_ordinal'] = True
        form = MultipleOccurrenceForm(data)
        assert form.is_valid(), form.errors.as_text()
        data['is_year_month_ordinal'] = False
        form = MultipleOccurrenceForm(data)
        assert form.is_valid(), form.errors.as_text()

    def test_yearly_freq_ord_true_requires_ordinal(self):
        invalid_ordinals = [None, 0]
        valid_ordinals = [1,2,3,4,-1]
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.YEARLY,

            'is_year_month_ordinal':  True,
            'year_month_ordinal_day': self.weekday_long['Tuesday'],
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=YEARLY, is_year_month_ordinal=True and no "
            "year_month_ordinal key valid."
        )
        for o in invalid_ordinals:
            data['year_month_ordinal'] = o
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid year_month_ordinal value %s identified as valid" % 0
            )
        for o in valid_ordinals:
            data['year_month_ordinal'] = o
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_yearly_freq_ord_true_requires_ordinal_day(self):
        invalid_ordinal_days = [None, 0]
        valid_ordinal_days = self.weekday_long.values()
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.YEARLY,

            'is_year_month_ordinal':  True,
            'year_month_ordinal':     '1',
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=YEARLY, is_year_month_ordinal=True and no "
            "year_month_ordinal_day key valid."
        )
        for d in invalid_ordinal_days:
            data['year_month_ordinal_day'] = d
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid year_month_ordinal_day value %s identified "
                "as valid" % d
            )
        for d in valid_ordinal_days:
            data['year_month_ordinal_day'] = d
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    def test_yearly_freq_ord_false_requires_year_months(self):
        valid_months = (
            [[i] for i in range(1,13)] +
            [[1,2], [11,12], [1,2,3,4,5,6], [7,8,9,10,11,12]]
        )
        invalid_months = (
            None, [None], [0], [13], [20], [0,1,2], [10,11,12,13]
        )
        data = {
            'day':                    self.tomorrow_str,
            'start_time_delta':       '28800',
            'end_time_delta':         '29700',

            'repeats':                'count',
            'count':                  7,

            'freq':                   rrule.YEARLY,

            'is_year_month_ordinal':  False,
        }
        form = MultipleOccurrenceForm(data)
        assert not form.is_valid(), (
            "form with freq=YEARLY, is_year_month_ordinal=False and no "
            "years_months key valid."
        )
        for m in invalid_months:
            data['year_months'] = m
            form = MultipleOccurrenceForm(data)
            assert not form.is_valid(), (
                "Invalid year_months value %s identified as valid" % m
            )
        for m in valid_months:
            data['year_months'] = m
            form = MultipleOccurrenceForm(data)
            assert form.is_valid(), form.errors.as_text()

    # Mis-matched groups shouldn't validate?

    # Combination where ordinal AND ordinal_day not provided?

    # Ensure that the right objects are created when BOTH variant .n's are
    # provided.

    # Test groups: atm, Frequencies are EITHER 1,2,3,4 - but that's only
    # because of the widget. What happens when multiple options are available?

    # How are duplicate 'each_month_day' values handled? Introduce clean_field
    # method which tries to coerce to set?

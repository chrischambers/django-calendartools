from datetime import date, timedelta
from django.test import TestCase
from nose.tools import *
from calendartools.forms import MultipleOccurrenceForm

class TestMultipleOccurrenceForm(TestCase):
    def setUp(self):
        today = date.today()
        tomorrow = (today + timedelta(1)).strftime('%Y-%m-%d')
        self.data = {
             'day':                    tomorrow,
             'start_time_delta':       '28800',
             'end_time_delta':         '29700',
             'year_month_ordinal_day': '2',
             'month_ordinal_day':      '2',
             'year_month_ordinal':     '1',
             'month_option':           'each',
             'repeats':                'count',
             'freq':                   '2',
             'month_ordinal':          '1',
        }

    def test_with_good_inputs(self):
        form = MultipleOccurrenceForm(self.data)
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_initial_dtstart(self):
        pass

    def test_build_rrule_params(self):
        pass


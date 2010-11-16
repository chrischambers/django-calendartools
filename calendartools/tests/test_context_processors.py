from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import *
from datetime import datetime, date
from calendartools.periods import Day

class TestContextProcessors(TestCase):
    def test_current_datetime(self):
        expected = date.today()
        response = self.client.get(reverse('event-list'), follow=True)
        now      = response.context['now']
        today    = response.context['today']

        assert isinstance(now, datetime)
        assert isinstance(today, Day)
        assert_equal(today, expected)
        assert_equal(now.date(), expected)

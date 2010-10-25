from datetime import timedelta, time
from django.contrib.auth.models import User
from django.test import TestCase
from nose.tools import *
from calendartools.defaults import (
    default_permission_check,
    timeslot_options,
    timeslot_offset_options
)


class TestPermissionCheck(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='TestyMcTesterson')
        self.user.set_password('password')
        self.user.save()
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )
        self.mock_request = lambda *a, **kw: True
        self.mock_request.user = self.user

    def test_default_permission_check(self):
        assert not default_permission_check(self.mock_request)
        self.user.is_staff = True
        self.user.save()
        assert default_permission_check(self.mock_request)


class TestTimeSlotOptions(TestCase):
    def setUp(self):
        self.inputs = {
             'interval':   timedelta(minutes=15),
             'start_time': time(12),
             'end_delta':  timedelta(hours=1),
             'fmt':        '%I:%M %p'
        }
        self.expected = [
            ('12:00:00', '12:00 PM'),
            ('12:15:00', '12:15 PM'),
            ('12:30:00', '12:30 PM'),
            ('12:45:00', '12:45 PM'),
            ('13:00:00', '01:00 PM'),
        ]

    def test_time_slot_options(self):
        actual = timeslot_options(**self.inputs)
        assert_equal(self.expected, actual)


class TestTimeSlotOptionsHourly(TestTimeSlotOptions):
    def setUp(self):
        self.inputs = {
             'interval':   timedelta(hours=1),
             'start_time': time(11),
             'end_delta':  timedelta(hours=3),
             'fmt':        '%I:%M %p'
        }
        self.expected = [
            ('11:00:00', '11:00 AM'),
            ('12:00:00', '12:00 PM'),
            ('13:00:00', '01:00 PM'),
            ('14:00:00', '02:00 PM'),
        ]


class TestTimeSlotOptionsFormatting(TestTimeSlotOptions):
    def setUp(self):
        self.inputs = {
             'interval':   timedelta(minutes=30),
             'start_time': time(23),
             'end_delta':  timedelta(hours=2),
             'fmt':        '%H:%M:%S'
        }
        self.expected = [
            ('23:00:00', '23:00:00'),
            ('23:30:00', '23:30:00'),
            ('00:00:00', '00:00:00'),
            ('00:30:00', '00:30:00'),
            ('01:00:00', '01:00:00'),
        ]


class TestTimeSlotOffsetOptions(TestCase):
    def setUp(self):
        self.inputs = {
             'interval':   timedelta(minutes=15),
             'start_time': time(12),
             'end_delta':  timedelta(hours=1),
             'fmt':        '%I:%M %p'
        }
        self.expected = [
            (43200, '12:00 PM'), # 12h * (60m * 60s)
            (44100, '12:15 PM'),
            (45000, '12:30 PM'),
            (45900, '12:45 PM'),
            (46800, '01:00 PM'),
        ]

    def test_time_slot_offset_options(self):
        actual = timeslot_offset_options(**self.inputs)
        assert_equal(self.expected, actual)


class TestTimeSlotOffsetOptionsHourly(TestTimeSlotOffsetOptions):
    def setUp(self):
        self.inputs = {
             'interval':   timedelta(hours=1),
             'start_time': time(11),
             'end_delta':  timedelta(hours=3),
             'fmt':        '%I:%M %p'
        }
        self.expected = [
            (39600, '11:00 AM'),
            (43200, '12:00 PM'),
            (46800, '01:00 PM'),
            (50400, '02:00 PM'),
        ]

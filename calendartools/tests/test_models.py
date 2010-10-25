from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from calendartools.models import Event, Occurrence
from nose.tools import *

class TestOccurrence(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )

    def test_finish_must_be_greater_than_start(self):
        start = datetime.utcnow()
        for finish in [start, start - timedelta(microseconds=1)]:
            assert_raises(
                ValidationError,
                Occurrence.objects.create,
                event=self.event, start=start, finish=finish
            )
        Occurrence.objects.create(
            event=self.event,
            start=start,
            finish=start + timedelta(microseconds=1)
        )


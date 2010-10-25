from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from calendartools.models import Event, Occurrence
from nose.tools import *


class TestEvent(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )

    def test_add_occurrences_basic(self):
        start = datetime.now()
        finish = start + timedelta(hours=2)
        self.event.add_occurrences(start, finish)
        assert_equal(self.event.occurrences.count(), 1)
        assert_equal(
            self.event.occurrences.latest().start.replace(microsecond=0),
            self.start.replace(microsecond=0)
        )
        assert_equal(
            self.event.occurrences.latest().finish.replace(microsecond=0),
            self.finish.replace(microsecond=0)
        )

    def test_add_occurrences_with_count(self):
        start = datetime.now()
        finish = start + timedelta(hours=2)
        self.event.add_occurrences(start, finish, count=3)
        assert_equal(self.event.occurrences.count(), 3)
        expected = [start, start + timedelta(1), start + timedelta(2)]
        expected = set([dt.replace(microsecond=0) for dt in expected])
        actual = set(self.event.occurrences.values_list('start', flat=True))
        assert_equal(expected, actual)

    def test_add_occurrences_with_until(self):
        start = datetime.now()
        finish = start + timedelta(hours=2)
        until = start + timedelta(5)
        self.event.add_occurrences(start, finish, until=until)
        assert_equal(self.event.occurrences.count(), 6)


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


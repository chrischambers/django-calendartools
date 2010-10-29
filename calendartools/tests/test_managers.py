from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from nose.tools import *
from calendartools.models import Event, Occurrence


class TestEventManager(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')

        self.inactive_event = Event.objects.create(
            name='Event', slug='inactive-event', creator=self.creator,
            status=Event.INACTIVE
        )
        self.hidden_event = Event.objects.create(
            name='Event', slug='hidden-event', creator=self.creator,
            status=Event.HIDDEN
        )
        self.cancelled_event = Event.objects.create(
            name='Event', slug='cancelled-event', creator=self.creator,
            status=Event.CANCELLED
        )
        self.published_event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )

    def test_visible_method(self):
        pass

    def _test_status_properties(self, prop, status):
        assert_equal(
            set(getattr(Event.objects, prop)),
            set(Event.objects.filter(status=status))
        )

    def test_inactive_property(self):
        assert_equal(
            set(Event.objects.inactive),
            set(Event.objects.filter(status=Event.INACTIVE))
        )

    def test_hidden_property(self):
        assert_equal(
            set(Event.objects.hidden),
            set(Event.objects.filter(status=Event.HIDDEN))
        )

    def test_cancelled_property(self):
        assert_equal(
            set(Event.objects.cancelled),
            set(Event.objects.filter(status=Event.CANCELLED))
        )

    def test_published_property(self):
        assert_equal(
            set(Event.objects.published),
            set(Event.objects.filter(status=Event.PUBLISHED))
        )


class TestOccurrenceManager(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)

        self.inactive_occurrence = Occurrence.objects.create(
            event=self.event, start=self.start, finish=self.finish,
            status=Occurrence.INACTIVE
        )
        self.hidden_occurrence = Occurrence.objects.create(
            event=self.event, start=self.start, finish=self.finish,
            status=Occurrence.HIDDEN
        )
        self.cancelled_occurrence = Occurrence.objects.create(
            event=self.event, start=self.start, finish=self.finish,
            status=Occurrence.CANCELLED
        )
        self.published_occurrence = Occurrence.objects.create(
            event=self.event, start=self.start, finish=self.finish,
            status=Occurrence.PUBLISHED
        )

    def _test_status_properties(self, prop, status):
        assert_equal(
            set(getattr(Occurrence.objects, prop)),
            set(Occurrence.objects.filter(status=status))
        )

    def test_inactive_property(self):
        assert_equal(
            set(Occurrence.objects.inactive),
            set(Occurrence.objects.filter(status=Occurrence.INACTIVE))
        )

    def test_hidden_property(self):
        assert_equal(
            set(Occurrence.objects.hidden),
            set(Occurrence.objects.filter(status=Occurrence.HIDDEN))
        )

    def test_cancelled_property(self):
        assert_equal(
            set(Occurrence.objects.cancelled),
            set(Occurrence.objects.filter(status=Occurrence.CANCELLED))
        )

    def test_published_property(self):
        assert_equal(
            set(Occurrence.objects.published),
            set(Occurrence.objects.filter(status=Occurrence.PUBLISHED))
        )

from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from nose.tools import *
from calendartools.models import Event, Occurrence


class TestCommonManager(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')

        self.events = []
        for status, label in Event.STATUS_CHOICES:
            self.events.append(Event.objects.create(
                name='Event',
                slug='%s-event' % label.lower(),
                creator=self.creator,
                status=status
            ))

        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)

        self.occurrence = []
        for status, label in Occurrence.STATUS_CHOICES:
            self.occurrence.append(Occurrence.objects.create(
                event=self.events[0], start=self.start, finish=self.finish,
                status=status
            ))
        self.model = Event

    def _test_status_properties(self, prop, status):
        assert_equal(
            set(getattr(self.model.objects, prop)),
            set(self.model.objects.filter(status=status))
        )

    def test_inactive_property(self):
        self._test_status_properties('inactive', self.model.INACTIVE)

    def test_hidden_property(self):
        self._test_status_properties('hidden', self.model.HIDDEN)

    def test_cancelled_property(self):
        self._test_status_properties('cancelled', self.model.CANCELLED)

    def test_published_property(self):
        self._test_status_properties('published', self.model.PUBLISHED)


class TestEventManager(TestCommonManager):
    def setUp(self):
        super(TestEventManager, self).setUp()

    def test_visible_method(self):
        pass


class TestOccurrenceManager(TestCommonManager):
    def setUp(self):
        super(TestOccurrenceManager, self).setUp()
        self.model = Occurrence

    def test_visible_method(self):
        pass

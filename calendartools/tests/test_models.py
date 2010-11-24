from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from calendartools.models import Calendar, Event, Occurrence, Attendance
from calendartools.exceptions import MaxOccurrenceCreationsExceeded
from calendartools import defaults
from calendartools.signals import collect_occurrence_validators
from calendartools.validators import BaseValidator
from nose.tools import *


class TestEventBase(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)
        self.occurrence = self.event.add_occurrences(
            self.calendar, self.start, self.finish)[0]

    def test_status_slug(self):
        mapping = {1: 'inactive', 2: 'hidden', 3: 'cancelled', 4: 'published'}
        for num in mapping:
            self.calendar.status = num
            self.event.status = num
            self.occurrence.status = num
            assert_equal(self.calendar.status_slug, mapping[num])
            assert_equal(self.event.status_slug, mapping[num])
            assert_equal(self.occurrence.status_slug, mapping[num])


class TestEvent(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)

    def test_add_occurrences_basic(self):
        self.event.add_occurrences(self.calendar, self.start, self.finish)
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
        self.event.add_occurrences(self.calendar, self.start, self.finish, count=3)
        assert_equal(self.event.occurrences.count(), 3)
        expected = [
            self.start,
            self.start + timedelta(1),
            self.start + timedelta(2)
        ]
        expected = set([dt.replace(microsecond=0) for dt in expected])
        actual = set(self.event.occurrences.values_list('start', flat=True))
        assert_equal(expected, actual)
        assert_equal(
            set(Occurrence.objects.filter(calendar=self.calendar)),
            set(Occurrence.objects.all()),
        )

    def test_add_occurrences_with_until(self):
        until = self.start + timedelta(5)
        self.event.add_occurrences(self.calendar, self.start, self.finish, until=until)
        assert_equal(self.event.occurrences.count(), 6)

    def test_add_occurrences_with_commit_false(self):
        occurrences = self.event.add_occurrences(
            self.calendar, self.start, self.finish, commit=False
        )
        assert_equal(self.event.occurrences.count(), 0)
        assert_equal(len(occurrences), 1)
        assert not occurrences[0].pk

        occurrences = self.event.add_occurrences(
            self.calendar, self.start, self.finish, count=3, commit=False
        )
        assert_equal(self.event.occurrences.count(), 0)
        assert_equal(len(occurrences), 3)
        assert_equal(
            [o.pk for o in occurrences],
            [None, None, None]
        )

    def test_add_occurrences_maximum_creation_count_exceeded(self):
        assert_raises(MaxOccurrenceCreationsExceeded,
            self.event.add_occurrences,
            self.calendar, self.start, self.finish, commit=False,
            count=defaults.MAX_OCCURRENCE_CREATION_COUNT + 1
        )

    def test_is_cancelled_property(self):
        assert not self.event.is_cancelled
        occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(microseconds=1)
        )
        occurrence.status = occurrence.CANCELLED
        occurrence.save()
        assert not self.event.is_cancelled
        self.event.status = self.event.CANCELLED
        self.event.save()
        self.event = Event.objects.get(pk=self.event.pk)
        assert self.event.is_cancelled


class TestOccurrence(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.start = datetime.now() + timedelta(minutes=30)

    def test_finish_must_be_greater_than_start(self):
        for finish in [self.start, self.start - timedelta(microseconds=1)]:
            assert_raises(
                ValidationError,
                Occurrence.objects.create,
                calendar=self.calendar, event=self.event,
                start=self.start, finish=finish
            )
        Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(microseconds=1)
        )

    def test_created_occurrences_must_occur_in_future(self):
        start = datetime.now()
        finish = start + timedelta(hours=2)
        assert_raises(
            ValidationError,
            Occurrence.objects.create,
            event=self.event, start=start - timedelta.resolution, finish=finish
        )

    def test_validation_with_missing_start(self):
        occurrence = Occurrence(
            calendar=self.calendar, event=self.event, start=self.start
        )
        assert_raises(ValidationError, occurrence.save)

    def test_validation_with_missing_end(self):
        occurrence = Occurrence(
            calendar=self.calendar, event=self.event, finish=self.start
        )
        assert_raises(ValidationError, occurrence.save)

    def test_updated_occurrences_need_not_occur_in_future(self):
        occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(hours=2)
        )
        occurrence.start = datetime.now() - timedelta.resolution
        occurrence.finish = occurrence.start + timedelta(hours=2)
        try:
            occurrence.save()
        except ValidationError, e:
            self.fail(
                'Editing Occurrence triggers must-occur-in-future validation:'
                '\n%s' % e
            )

    def test_pluggable_validators_priority(self):
        class AngryValidator(BaseValidator):
            priority = 9000
            error_message = "Angry Validator is Angry."

            def validate(self):
                raise ValidationError(self.error_message)

        occurrence = Occurrence(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start # also fails finish > start check.
        )
        try:
            collect_occurrence_validators.connect(AngryValidator)
            occurrence.save()
            self.fail('ValidationError not triggered')
        except ValidationError, e:
            assert_equal(e.messages[0], AngryValidator.error_message)
            AngryValidator.priority = -1
            try:
                occurrence.save()
                self.fail('ValidationError not triggered')
            except ValidationError, e:
                assert_not_equal(e.messages[0], AngryValidator.error_message)
        finally:
            collect_occurrence_validators.disconnect(AngryValidator)

    def test_is_cancelled_property(self):
        occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(microseconds=1)
        )
        assert not occurrence.is_cancelled
        occurrence.status = occurrence.CANCELLED
        occurrence.save()
        occurrence = Occurrence.objects.get(pk=occurrence.pk)
        assert occurrence.is_cancelled
        occurrence.status = occurrence.PUBLISHED
        occurrence.save()
        assert not occurrence.is_cancelled
        self.event.status = self.event.CANCELLED
        self.event.save()
        occurrence = Occurrence.objects.get(pk=occurrence.pk)
        assert occurrence.is_cancelled
        self.event.status = self.event.PUBLISHED
        self.event.save()
        self.calendar.status = Calendar.CANCELLED
        self.calendar.save()
        occurrence = Occurrence.objects.get(pk=occurrence.pk)
        assert occurrence.is_cancelled

    def test_name_property(self):
        occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(microseconds=1)
        )
        assert_equal(occurrence.name, self.event.name)

    def test_description_property(self):
        occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(microseconds=1)
        )
        assert_equal(occurrence.description, self.event.description)


class TestAttendance(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='TestyMcTesterson')
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(minutes=30)
        self.occurrence = self.event.add_occurrences(
            self.calendar, self.start, self.finish)[0]

    def test_create_attendance(self):
        att = Attendance.objects.create(
            user=self.user, occurrence=self.occurrence
        )
        assert_equal(att.status, Attendance.BOOKED)

    def test_cannot_attend_finished_occurrences(self):
        self.occurrence.start = self.occurrence.start - timedelta(1)
        self.occurrence.finish = self.occurrence.finish - timedelta(1)
        self.occurrence.save()
        self.assertRaises(ValidationError, Attendance.objects.create,
            user=self.user, occurrence=self.occurrence
        )

    def test_only_one_active_attendance_record_for_user_occurrence(self):
        att = Attendance(user=self.user, occurrence=self.occurrence)
        for status in [Attendance.BOOKED, Attendance.ATTENDED]:
            att.status = att.ATTENDED
            att.save()
            self.assertRaises(ValidationError, Attendance.objects.create,
                user=self.user, occurrence=self.occurrence
            )
        for status in [Attendance.INACTIVE, Attendance.CANCELLED]:
            att.status = status
            att.save()
            att2 = Attendance.objects.create(
                user=self.user, occurrence=self.occurrence
            )
            att2.delete()

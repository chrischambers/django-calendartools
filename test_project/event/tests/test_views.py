from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase

from event.models import (
    Calendar, Event, Occurrence, Attendance
)
from calendartools import defaults, signals, views
from calendartools.forms import (
    EventForm,
    MultipleOccurrenceForm,
    ConfirmOccurrenceForm
)
from calendartools.validators import BaseValidator
from calendartools.validators.defaults.attendance import (
    CannotAttendFutureEventsValidator
)

from nose.tools import *


class TestTemplateOverrides(TestCase):

    def setUp(self):
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')

    def test_day_calendar_override(self):
        url = reverse('day-calendar', args=[self.calendar.slug, 1982, 'aug', 17])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'event/calendar/day.html')

    def test_day_agenda_override(self):
        url = reverse('day-agenda', args=[self.calendar.slug, 1982, 'aug', 17])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'event/agenda/day.html')

class TestEventListView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def test_event_list_context(self):
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(
            set(response.context['object_list']),
            set(Event.objects.all())
        )

    def test_published_events_listed(self):
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.name)

    def test_inactive_events_not_included(self):
        self.event.status = self.event.STATUS.inactive
        self.event.save()
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert not response.context['object_list']

    def test_hidden_events_not_included(self):
        self.event.status = self.event.STATUS.hidden
        self.event.save()
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert not response.context['object_list']
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert not response.context['object_list']

    def test_cancelled_events_included(self):
        self.event.status = self.event.STATUS.cancelled
        self.event.save()
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert_equal(
            set(response.context['object_list']),
            set(Event.objects.all())
        )


class TestEventDetailView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.change_event_perm = Permission.objects.get(
            content_type__app_label=defaults.CALENDAR_APP_LABEL,
            codename='change_event'
        )
        self.add_occurrence_perm = Permission.objects.get(
            content_type__app_label=defaults.CALENDAR_APP_LABEL,
            codename='add_occurrence'
        )
        self.start = datetime.utcnow() + timedelta(hours=2)
        self.occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(hours=2)
        )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def test_event_detail_context(self):
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.context['event'], self.event)

    def test_inactive_event_detail_not_displayed(self):
        self.event.status = self.event.STATUS.inactive
        self.event.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_event_detail_not_displayed(self):
        self.event.status = self.event.STATUS.hidden
        self.event.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_event_detail_displayed_for_permitted_users(self):
        self.event.status = self.event.STATUS.hidden
        self.event.save()
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_cancelled_event_detail_displayed(self):
        self.event.status = self.event.STATUS.cancelled
        self.event.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_published_event_detail_displayed(self):
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_edit_form_displayed_only_for_correct_perm(self):
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert not response.context[-1].get('event_form')

        self.user.user_permissions.add(self.change_event_perm)
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert isinstance(response.context[-1].get('event_form'), EventForm)

    def test_occurrences_form_displayed_only_for_correct_perm(self):
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert not response.context[-1].get('recurrence_form')

        self.user.user_permissions.add(self.add_occurrence_perm)
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert isinstance(
            response.context[-1].get('recurrence_form'), MultipleOccurrenceForm
        )

    def test_post_to_edit_form_only_works_for_correct_perm(self):
        response = self.client.post(
            reverse('event-detail', args=(self.event.slug,)), data={'_update': 1}
        )
        assert_equal(response.status_code, 400)

        self.user.user_permissions.add(self.change_event_perm)
        response = self.client.post(
            reverse('event-detail', args=(self.event.slug,)), data={'_update': 1}
        )
        assert_equal(response.status_code, 200)

    def test_post_to_occurrences_form_only_works_for_correct_perm(self):
        data = {
             '_add':             1,
             'day':              '2010-10-26',
             'start_time_delta': 3600,
             'end_time_delta':   7200
        }
        response = self.client.post(
            reverse('event-detail', args=(self.event.slug,)), data=data
        )
        assert_equal(response.status_code, 400)

        self.user.user_permissions.add(self.add_occurrence_perm)
        response = self.client.post(
            reverse('event-detail', args=(self.event.slug,)), data=data
        )
        assert_equal(response.status_code, 200)

    def test_list_occurrences(self):
        for status, label in Occurrence.STATUS:
            Occurrence.objects.create(
                calendar=self.calendar,
                event=self.event,
                start=self.start,
                finish=self.start + timedelta(hours=2),
                status=status
            )
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(
            set(response.context['occurrences']),
            set(Occurrence.objects.visible())
        )


class TestEventDetailView2(TestCase):
    urls = 'event.tests.test_urls.event_detail_no_list_occurrences'

    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.start = datetime.utcnow() + timedelta(hours=2)

    def test_list_occurrences(self):
        for status, label in Occurrence.STATUS:
            Occurrence.objects.create(
                calendar=self.calendar,
                event=self.event,
                start=self.start,
                finish=self.start + timedelta(hours=2),
                status=status
            )
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert not response.context[-1].get('occurrences')


class TestOccurrenceDetailView(TestCase):
    urls = 'event.tests.test_urls.occurrence_detail_show_attending'

    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        start = datetime.now() + timedelta(1)
        self.occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=start,
            finish=start + timedelta(hours=2)
        )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def test_occurrence_detail_context(self):
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.context['event'], self.event)
        assert_equal(response.context['attendance'],
                     Attendance(user=self.user, occurrence=self.occurrence))

    def test_attendance_context_only_populated_with_desired_statuses(self):
        attendance = Attendance(user=self.user, occurrence=self.occurrence)
        try:
            signals.collect_validators.disconnect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )
            for status in (Attendance.STATUS.booked, Attendance.STATUS.attended):
                attendance.status = status
                attendance.save()
                response = self.client.get(
                    reverse('occurrence-detail',
                            args=(self.event.slug, self.occurrence.pk)), follow=True
                )
                assert_equal(response.context['attendance'], attendance)
            for status in (Attendance.STATUS.inactive, Attendance.STATUS.cancelled):
                attendance.status = status
                attendance.save()
                response = self.client.get(reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
                )
                assert_not_equal(response.context['attendance'], attendance)
        finally:
            signals.collect_validators.connect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )

    def test_occurrence_context_with_show_attending(self):
        response = self.client.get(
            reverse('show-attending',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_false(bool(response.context['attending']))
        attendance = Attendance.objects.create(
            user=self.user,
            occurrence=self.occurrence
        )
        response = self.client.get(
            reverse('show-attending',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal([i for i in response.context['attending']], [attendance])

    def test_attended_status_does_not_display_form(self):
        try:
            signals.collect_validators.disconnect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )
            attendance = Attendance.objects.create(
                user=self.user,
                occurrence=self.occurrence,
                status=Attendance.STATUS.attended
            )
            response = self.client.get(reverse('occurrence-detail',
                args=(self.event.slug, self.occurrence.pk)), follow=True
            )
            assert_not_in('form', response.context[-1])
        finally:
            signals.collect_validators.connect(
                CannotAttendFutureEventsValidator, sender=Attendance
            )

    def test_book_attendance(self):
        assert not Attendance.objects.exists()
        response = self.client.post(reverse('occurrence-detail',
            args=(self.event.slug, self.occurrence.pk)), data={}, follow=True
        )
        attendance = Attendance.objects.get()
        assert_equal(attendance.user, self.user)
        assert_equal(attendance.occurrence, self.occurrence)
        assert_equal(attendance.status, Attendance.STATUS.booked)

    def test_cancel_attendance(self):
        assert not Attendance.objects.exists()
        response = self.client.post(reverse('occurrence-detail',
            args=(self.event.slug, self.occurrence.pk)), data={}, follow=True
        )
        assert_equal(Attendance.objects.count(), 1)
        attendance = Attendance.objects.get()
        assert_equal(attendance.status, Attendance.STATUS.booked)
        response = self.client.post(reverse('occurrence-detail',
            args=(self.event.slug, self.occurrence.pk)), data={}, follow=True
        )
        attendance = Attendance.objects.get()
        assert_equal(attendance.status, Attendance.STATUS.cancelled)

    def test_occurrence_detail(self):
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description, count=1)
        self.assertContains(response, self.event.name)

    def test_inactive_occurrence_detail_not_displayed(self):
        self.occurrence.status = self.occurrence.STATUS.inactive
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_not_displayed(self):
        self.occurrence.status = self.occurrence.STATUS.hidden
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_displayed_for_permitted_users(self):
        self.occurrence.status = self.occurrence.STATUS.hidden
        self.occurrence.save()
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_cancelled_occurrence_detail_displayed(self):
        self.occurrence.status = self.occurrence.STATUS.cancelled
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_published_occurrence_detail_displayed(self):
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_occurrence_with_inactive_event_not_displayed(self):
        self.event.status = self.event.STATUS.inactive
        self.event.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_occurrence_with_hidden_event_not_displayed(self):
        self.event.status = self.event.STATUS.hidden
        self.event.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_occurrence_with_hidden_event_displayed_for_permitted_users(self):
        self.event.status = self.event.STATUS.hidden
        self.event.save()
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)

    def test_occurrence_with_cancelled_event_displayed_as_cancelled(self):
        self.event.status = self.event.STATUS.cancelled
        self.event.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)
        self.assertContains(response, "This event has been cancelled")

    def test_cancelled_occurrence_with_published_event_displayed(self):
        self.occurrence.status = self.occurrence.STATUS.cancelled
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description)
        self.assertContains(response, self.event.name)


class TestConfirmOccurrenceView(TestCase):
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
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

        self.event  = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        self.event2 = Event.objects.create(
            name='Event', slug='other-event', creator=self.user
        )
        now     = datetime.now() - timedelta.resolution
        start   = now + timedelta(minutes=30)
        finish  = start + timedelta(hours=1)

        valid = Occurrence(
            calendar=self.calendar,
            event=self.event,
            start=start,
            finish=finish
        )
        valid2 = Occurrence(
            calendar=self.calendar,
            event=self.event2,
            start=start,
            finish=finish
        )
        invalid = Occurrence(
            calendar=self.calendar,
            event=self.event,
            start=now,
            finish=finish
        )

        self.valid   = [valid, valid2]
        self.invalid = [(invalid, 'Craziness went down.')]

        self.session_data = {
            'event':               self.event,
            'valid_occurrences':   self.valid,
            'invalid_occurrences': self.invalid
        }
        self.occurrence_key = 'occurrence_info'
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Waiting for this to land... http://code.djangoproject.com/ticket/10899
        # What SHOULD be as simple as this:
        # >>> self.client.session['email'] = 'foo@bar.com'
        # is currently this madness...
        from django.conf import settings
        from django.utils.importlib import import_module
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()  # we need to make load() work, or the cookie is worthless
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        session = self.client.session
        session[self.occurrence_key] = self.session_data
        session.save()
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def test_no_permission_redirects_to_event_list(self):
        self.user.user_permissions.remove(self.add_occurrence_perm)
        response = self.client.get(reverse('confirm-occurrences'), follow=True)
        self.assertRedirects(response, reverse('event-detail', args=[self.event.slug]))

    def test_no_session_data_redirects_to_event_list(self):
        session = self.client.session
        del session[self.occurrence_key]
        session.save()
        response = self.client.get(reverse('confirm-occurrences'), follow=True)
        self.assertRedirects(response, reverse('event-list'))

    def test_correct_session_data_shows_confirm_page(self):
        response = self.client.get(reverse('confirm-occurrences'), follow=True)
        assert_equal(response.status_code, 200)
        self.assertContains(response, 'Craziness went down', count=1)

    def test_correct_session_data_has_correct_context(self):
        response = self.client.get(reverse('confirm-occurrences'), follow=True)
        assert_equal(response.context[-1].get('valid_occurrences'), self.valid)
        assert_equal(response.context[-1].get('invalid_occurrences'), self.invalid)
        assert isinstance(response.context[-1].get('form'), ConfirmOccurrenceForm)

    def test_post_with_correct_data_saves_correct_records(self):
        assert_equal(Occurrence.objects.count(), 0)
        response = self.client.post(
            reverse('confirm-occurrences'), data={}, follow=True
        )
        self.assertRedirects(response, reverse('event-detail', args=[self.event.slug]))
        assert_equal(Occurrence.objects.count(), 2)
        assert not self.client.session.get(self.occurrence_key)


    def test_model_validation(self):
        # This handles situations where a condition changes between the time
        # that:
        # i) the MultipleOccurrenceForm is submitted and,
        # ii) the ConfirmOccurrenceForm is posted
        # which would causes one of the models to fail its validation checks.
        assert_equal(Occurrence.objects.count(), 0)
        response = self.client.get(
            reverse('confirm-occurrences'), follow=True
        )
        try:
            class Event2EventsNotAllowed(BaseValidator):
                priority = 9000
                error_message = "Event 'other-event' isn't allowed!"
                def validate(self):
                    if self.instance.event.slug == 'other-event':
                        raise ValidationError(self.error_message)

            self.validator = Event2EventsNotAllowed
            signals.collect_validators.connect(self.validator, sender=Occurrence)

            response = self.client.post(
                reverse('confirm-occurrences'), data={}, follow=True
            )
            self.assertRedirects(response, reverse('confirm-occurrences'))
            assert_equal(
                set(response.context[-1].get('valid_occurrences')),
                set([self.valid[0]])
            )
            assert_equal(
                set(response.context[-1].get('invalid_occurrences')),
                set([(self.valid[1], self.validator.error_message)]),
            )
            response = self.client.post(
                reverse('confirm-occurrences'), data={}, follow=True
            )
            assert_equal(Occurrence.objects.count(), 1)
            assert not self.client.session.get(self.occurrence_key)

        finally:
            signals.collect_validators.disconnect(self.validator, sender=Occurrence)


class TestCalendarVisibility(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar  = Calendar.objects.create(name='Test1', slug='t1')
        self.calendar2 = Calendar.objects.create(name='Test2', slug='t2')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        now = datetime.now() + timedelta(days=1)
        self.occurrence = Occurrence.objects.create(
            calendar=self.calendar,
            event=self.event,
            start=now,
            finish=now + timedelta(hours=2)
        )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )
        self.url_params = (
            ('agenda', {'slug': self.calendar.slug}),
            ('calendar-detail', {'slug': self.calendar.slug}),

            ('year-calendar', {
                'slug': self.calendar.slug,
                'year': 2010
            }),
            ('month-calendar', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
            }),
            ('small-month-calendar', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
            }),
            ('tri-month-calendar', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
            }),
            ('week-calendar', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'week':   10,
            }),
            ('day-calendar', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
                'day':   10,
            }),
            ('year-agenda', {
                'slug': self.calendar.slug,
                'year': 2010
            }),
            ('month-agenda', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
            }),
            ('week-agenda', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'week':   10,
            }),
            ('day-agenda', {
                'slug':  self.calendar.slug,
                'year':  2010,
                'month': 'nov',
                'day':   10,
            }),
        )
        self.urls = [reverse(url, kwargs=kwargs) for
                     (url, kwargs) in self.url_params]

    def test_calendar_list_displays_cancelled_and_above(self):
        for state in (Calendar.STATUS.inactive, Calendar.STATUS.hidden):
            Calendar.objects.all().update(status=state)
            response = self.client.get(reverse('calendar-list'), follow=True)
            assert_equal(len(response.context[-1].get('object_list')), 0)

        for state in (Calendar.STATUS.cancelled, Calendar.STATUS.published):
            Calendar.objects.all().update(status=state)
            response = self.client.get(reverse('calendar-list'), follow=True)
            assert_equal(len(response.context[-1].get('object_list')), 2)

    def test_calendar_list_displays_hidden_for_staff(self):
        Calendar.objects.all().update(status=Calendar.STATUS.hidden)

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(reverse('calendar-list'), follow=True)
        assert_equal(len(response.context[-1].get('object_list')), 2)

        self.user.is_staff = True
        self.user.is_superuser = False
        self.user.save()
        response = self.client.get(reverse('calendar-list'), follow=True)
        assert_equal(len(response.context[-1].get('object_list')), 2)

    def test_normal_user_cannot_see_inactive_calendars(self):
        Calendar.objects.all().update(status=Calendar.STATUS.inactive)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(404, response.status_code)

    def test_normal_user_cannot_see_hidden_calendars(self):
        Calendar.objects.all().update(status=Calendar.STATUS.hidden)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(404, response.status_code)

    def test_normal_user_can_see_cancelled_calendars(self):
        Calendar.objects.all().update(status=Calendar.STATUS.cancelled)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(200, response.status_code)

    def test_normal_user_can_see_published_calendars(self):
        Calendar.objects.all().update(status=Calendar.STATUS.published)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(200, response.status_code)

    def test_superuser_can_see_hidden_calendars(self):
        self.user.is_superuser = True
        self.user.save()
        Calendar.objects.all().update(status=Calendar.STATUS.hidden)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(200, response.status_code)

    def test_staff_user_can_see_hidden_calendars(self):
        self.user.is_staff = True
        self.user.save()
        Calendar.objects.all().update(status=Calendar.STATUS.hidden)
        for url in self.urls:
            response = self.client.get(url, follow=True)
            assert_equal(200, response.status_code)


class TestCalendarViews(TestCase):
    urls = 'event.tests.test_urls.calendar_view_tests'

    def setUp(self):
        self.user = User.objects.create_user(
            'TestyMcTesterson',
            'Testy@test.com',
            'password'
        )
        self.calendar  = Calendar.objects.create(name='Test1', slug='t1')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        now = datetime.now()
        self.base_datetime = datetime(now.year + 1, 1, 7)
        self.datetimes = [
            self.base_datetime,
            self.base_datetime + relativedelta(days=1),
            self.base_datetime + relativedelta(weeks=1),
            self.base_datetime + relativedelta(months=1),
            self.base_datetime + relativedelta(months=2),
            self.base_datetime + relativedelta(months=5),
        ]
        for dt in self.datetimes:
            Occurrence.objects.create(
                calendar=self.calendar,
                event=self.event,
                start=dt,
                finish=dt + timedelta(hours=2)
            )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )
        self.url_params = [
            ('year-calendar', {
                'slug': self.calendar.slug,
                'year': self.base_datetime.year
            }),
            ('tri-month-calendar', {
                'slug':  self.calendar.slug,
                'year':  self.base_datetime.year,
                'month': self.base_datetime.strftime('%b').lower(),
            }),
            ('small-month-calendar', {
                'slug':  self.calendar.slug,
                'year':  self.base_datetime.year,
                'month': self.base_datetime.strftime('%b').lower(),
            }),
            ('month-calendar', {
                'slug':  self.calendar.slug,
                'year':  self.base_datetime.year,
                'month': self.base_datetime.strftime('%b').lower(),
            }),
            ('week-calendar', {
                'slug':  self.calendar.slug,
                'year':  self.base_datetime.year,
                'week':  1,
            }),
            ('day-calendar', {
                'slug':  self.calendar.slug,
                'year':  self.base_datetime.year,
                'month': self.base_datetime.strftime('%b').lower(),
                'day':   self.base_datetime.day
            }),
        ]
        self.urls = [reverse(url, kwargs=kwargs) for
                     (url, kwargs) in self.url_params]
        self.expected_occurrences = [6, 4, 3, 3, 2, 1]

    def test_date(self):
        o = views.calendars.YearView(slug='foo', year='2010')
        assert_equal(o.date, date(2010, 1, 1))
        # Special case: the TriMonthView displays as though the middle month is
        # the main focus, but its actual start period runs from the first month:
        o = views.calendars.TriMonthView(slug='foo', year='2010', month='nov')
        assert_equal(o.date, date(2010, 10, 1))
        o = views.calendars.MonthView(slug='foo', year='2010', month='nov')
        assert_equal(o.date, date(2010, 11, 1))
        o = views.calendars.WeekView(slug='foo', year='2010', week='1')
        assert_equal(o.date, date(2010, 1, 4)) # Monday
        o = views.calendars.DayView(slug='foo', year='2010', month='aug', day='17')
        assert_equal(o.date, date(2010, 8, 17))

    def test_occurrences_populated_correctly(self):
        for amount, url in zip(self.expected_occurrences, self.urls):
            response = self.client.get(url, follow=True)
            assert_equal(response.context[-1].get('object_list').count(), amount)

    def test_allow_future(self):
        response = self.client.get(
            reverse('year-calendar-no-future',
                    kwargs=self.url_params[0][1]), follow=True)
        assert_equal(response.context[-1].get('object_list').count(), 0)

    def test_allow_empty(self):
        response = self.client.get(
            reverse('year-calendar-no-empty', args=['foo', 2010]), follow=True)
        assert_equal(response.status_code, 404)

    def test_filters(self):
        for url_part in self.urls:
            for period in ['today', 'past']:
                url = '%s?period=%s' % (url_part, period)
                response = self.client.get(url, follow=True)
                assert_equal(response.context[-1].get('object_list').count(), 0)

        for amount, url in zip(self.expected_occurrences, self.urls):
            url = '%s?period=future' % url
            response = self.client.get(url, follow=True)
            assert_equal(response.context[-1].get('object_list').count(), amount)

    def test_size_context(self):
        small_urls = self.urls[:3]
        for url in self.urls:
            expected = 'small' if url in small_urls else None
            response = self.client.get(url, follow=True)
            assert_equal(response.context[-1].get('size'), expected)


class TestAgendaViews(TestCase):
    pass

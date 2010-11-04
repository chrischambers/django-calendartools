from datetime import datetime, timedelta

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase

from calendartools.models import Event, Occurrence
from calendartools import signals
from calendartools.forms import (
    EventForm,
    MultipleOccurrenceForm,
    ConfirmOccurrenceForm
)
from calendartools.validators import BaseValidator

from nose.tools import *

from dateutil.rrule import rrule, DAILY

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
        self.event.status = self.event.INACTIVE
        self.event.save()
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert not response.context['object_list']

    def test_hidden_events_not_included(self):
        self.event.status = self.event.HIDDEN
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
        self.event.status = self.event.CANCELLED
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
        self.event = Event.objects.create(
            name='The Test Event',
            slug='event-version-1',
            description="This is the description.",
            creator=self.user
        )
        self.change_event_perm = Permission.objects.get(
            content_type__app_label='calendartools',
            codename='change_event'
        )
        self.add_occurrence_perm = Permission.objects.get(
            content_type__app_label='calendartools',
            codename='add_occurrence'
        )
        self.start = datetime.utcnow() + timedelta(hours=2)
        self.occurrence = Occurrence.objects.create(
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(hours=2)
        )
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

    def tearDown(self):
        super(TestEventDetailView, self).tearDown()
        Occurrence.objects.all().delete()

    def test_event_detail_context(self):
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.context['event'], self.event)

    def test_inactive_event_detail_not_displayed(self):
        self.event.status = self.event.INACTIVE
        self.event.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_event_detail_not_displayed(self):
        self.event.status = self.event.HIDDEN
        self.event.save()
        response = self.client.get(
            reverse('event-detail', args=(self.event.slug,)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_event_detail_displayed_for_permitted_users(self):
        self.event.status = self.event.HIDDEN
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
        self.event.status = self.event.CANCELLED
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
        for status, label in Occurrence.STATUS_CHOICES:
            Occurrence.objects.create(
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
    urls = 'calendartools.tests.test_urls.event_detail_no_list_occurrences'

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
        self.start = datetime.utcnow() + timedelta(hours=2)

    def test_list_occurrences(self):
        for status, label in Occurrence.STATUS_CHOICES:
            Occurrence.objects.create(
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
        now = datetime.utcnow()
        self.occurrence = Occurrence.objects.create(
            event=self.event,
            start=now,
            finish=now + timedelta(hours=2)
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

    def test_occurrence_detail(self):
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 200)
        self.assertContains(response, self.event.description, count=1)
        self.assertContains(response, self.event.name)

    def test_inactive_occurrence_detail_not_displayed(self):
        self.occurrence.status = self.occurrence.INACTIVE
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_not_displayed(self):
        self.occurrence.status = self.occurrence.HIDDEN
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_displayed_for_permitted_users(self):
        self.occurrence.status = self.occurrence.HIDDEN
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
        self.occurrence.status = self.occurrence.CANCELLED
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
        self.event.status = self.event.INACTIVE
        self.event.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_occurrence_with_hidden_event_not_displayed(self):
        self.event.status = self.event.HIDDEN
        self.event.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_occurrence_with_hidden_event_displayed_for_permitted_users(self):
        self.event.status = self.event.HIDDEN
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
        self.event.status = self.event.CANCELLED
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
        self.occurrence.status = self.occurrence.CANCELLED
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
        self.add_occurrence_perm = Permission.objects.get(
            content_type__app_label='calendartools',
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
        valid   = Occurrence(event=self.event,  start=start, finish=finish)
        valid2  = Occurrence(event=self.event2, start=start, finish=finish)
        invalid = Occurrence(event=self.event,  start=now,   finish=finish)

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
        # which would causes one of the models fail its validation checks.
        assert_equal(Occurrence.objects.count(), 0)
        response = self.client.get(
            reverse('confirm-occurrences'), follow=True
        )
        try:
            class Event2EventsNotAllowed(BaseValidator):
                priority = 9000
                error_message = "Event 'other-event' isn't allowed!"
                def validate(self):
                    if self.sender.event.slug == 'other-event':
                        raise ValidationError(self.error_message)

            self.validator = Event2EventsNotAllowed
            signals.collect_occurrence_validators.connect(self.validator)

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
            signals.collect_occurrence_validators.disconnect(self.validator)


class TestOccurrenceDetailRedirect(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='TestyMcTesterson')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.user
        )
        now = datetime.utcnow()
        self.occurrence = Occurrence.objects.create(
            event=self.event,
            start=now,
            finish=now + timedelta(hours=2)
        )

    def test_occurrence_detail_redirect(self):
        """ ../2010/jan/1/event-slug/1/ ==> ../event-slug/1/"""
        start = self.occurrence.start
        url = '/%s/%s/%s/%s/%s/' % (
            start.year, start.strftime('%b').lower(),
            start.day, self.event.slug, self.occurrence.pk
        )
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('occurrence-detail',
            args=(self.event.slug, self.occurrence.pk)),
            status_code=301
        )

from calendartools.views.calendar import Calendar
class TestCalendar(TestCase):
    def setUp(self):
        self.start  = datetime(2009, 1, 1)
        self.finish = datetime(2010, 12, 1)
        self.cal = Calendar(self.start, self.finish)

    def test_init(self):
        assert_equal(self.cal.start, self.start)
        assert_equal(self.cal.finish, self.finish)

    def test_years_property(self):
        mapping = (
            ({ 'start':  datetime(2009, 12, 1),
               'finish': datetime(2010, 1, 1) },
             [datetime(2009, 1, 1,), datetime(2010, 1, 1)]),
            ({ 'start':  datetime(2009, 1, 1),
               'finish': datetime(2009, 12, 31) },
             [datetime(2009, 1, 1,)]),
            ({ 'start':  datetime(2008, 1, 1),
               'finish': datetime(2009, 7, 1) },
             [datetime(2008, 1, 1,), datetime(2009, 1, 1)]),
        )
        for inputs, expected in mapping:
            cal = Calendar(**inputs)
            res = []
            for year in cal.years:
                res.append(year)
            assert_equal(res, expected)

    def test_months_property(self):
        mapping = (
            ({ 'start':  datetime(2009, 12, 1),
               'finish': datetime(2010, 1, 1) },
             [datetime(2009, 12, 1,), datetime(2010, 1, 1)]),
            ({ 'start':  datetime(2009, 1, 1),
               'finish': datetime(2009, 12, 31) },
             [datetime(2009, 1 , 1,),
              datetime(2009, 2 , 1,),
              datetime(2009, 3 , 1,),
              datetime(2009, 4 , 1,),
              datetime(2009, 5 , 1,),
              datetime(2009, 6 , 1,),
              datetime(2009, 7 , 1,),
              datetime(2009, 8 , 1,),
              datetime(2009, 9 , 1,),
              datetime(2009, 10, 1,),
              datetime(2009, 11, 1,),
              datetime(2009, 12, 1,)]),
            ({ 'start':  datetime(2008, 1, 1),
               'finish': datetime(2009, 7, 1) },
             [datetime(2008, 1 , 1,),
              datetime(2008, 2 , 1,),
              datetime(2008, 3 , 1,),
              datetime(2008, 4 , 1,),
              datetime(2008, 5 , 1,),
              datetime(2008, 6 , 1,),
              datetime(2008, 7 , 1,),
              datetime(2008, 8 , 1,),
              datetime(2008, 9 , 1,),
              datetime(2008, 10, 1,),
              datetime(2008, 11, 1,),
              datetime(2008, 12, 1,),
              datetime(2009, 1, 1,),
              datetime(2009, 2, 1,),
              datetime(2009, 3, 1,),
              datetime(2009, 4, 1,),
              datetime(2009, 5, 1,),
              datetime(2009, 6, 1,),
              datetime(2009, 7, 1,),
             ]),
        )

        for inputs, expected in mapping:
            cal = Calendar(**inputs)
            res = []
            for month in cal.months:
                res.append(month)
            assert_equal(res, expected)

    def test_days(self):
        inputs = (
            {  'start':  datetime(2009, 12, 1),
               'finish': datetime(2010, 1, 1)   },
            {  'start':  datetime(2009, 1, 1),
               'finish': datetime(2009, 12, 31) },
            {  'start':  datetime(2008, 1, 1),
               'finish': datetime(2009, 7, 1)   },
        )

        for input in inputs:
            cal = Calendar(**input)
            res = []
            expected = list(rrule(DAILY, dtstart=input['start'], until=input['finish']))
            for day in cal.days:
                res.append(day)
            assert_equal(res, expected)

    def test_iterating_over_calendar_yields_years(self):
        mapping = (
            ({ 'start':  datetime(2009, 12, 1),
               'finish': datetime(2010, 1, 1) },
             [datetime(2009, 1, 1,), datetime(2010, 1, 1)]),
            ({ 'start':  datetime(2009, 1, 1),
               'finish': datetime(2009, 12, 31) },
             [datetime(2009, 1, 1,)]),
            ({ 'start':  datetime(2008, 1, 1),
               'finish': datetime(2009, 7, 1) },
             [datetime(2008, 1, 1,), datetime(2009, 1, 1)]),
        )
        for inputs, expected in mapping:
            cal = Calendar(**inputs)
            assert_equal(list(cal.years), list(iter(cal)))

    def test_cache_triggered_for_date_properties(self):
        cached_data = 'Hey Thar!'
        for prop in ['years', 'months', 'days']:
            setattr(self.cal, '_%s' % prop, cached_data)
            assert_equal(getattr(self.cal, prop), cached_data)

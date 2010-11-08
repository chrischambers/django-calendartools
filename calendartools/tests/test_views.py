from datetime import datetime, date, time, timedelta

from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase

from calendartools.models import Event, Occurrence
from calendartools import signals, defaults
from calendartools.forms import (
    EventForm,
    MultipleOccurrenceForm,
    ConfirmOccurrenceForm
)
from calendartools.validators import BaseValidator

from nose.tools import *

from dateutil.rrule import rrule, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY
from django.utils.dates import MONTHS, MONTHS_3, WEEKDAYS, WEEKDAYS_ABBR

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

from calendartools.views import Calendar, SimpleProxy, DateTimeProxy
class TestCalendar(TestCase):
    def setUp(self):
        self.start  = datetime(2009, 1, 1)
        self.finish = datetime(2010, 12, 1)
        self.cal = Calendar(self.start, self.finish)
        self.inputs = (
            {  'start':  datetime(2009, 12, 1),
               'finish': datetime(2010, 1, 1)   },
            {  'start':  datetime(2009, 1, 1),
               'finish': datetime(2009, 12, 31) },
            {  'start':  datetime(2008, 1, 15),
               'finish': datetime(2009, 7, 30)  },
        )

    def test_init(self):
        assert_equal(self.cal.start, self.start)
        assert_equal(self.cal.finish, self.finish)

    def _test_date_properties(self, prop, rrule_type, preprocess_start=None):
        for inputs in self.inputs:
            cal = Calendar(**inputs)
            res = []
            start = preprocess_start and preprocess_start(cal.start) or cal.start
            expected = list(rrule(rrule_type, dtstart=start, until=cal.finish))
            for dt in getattr(cal, prop):
                res.append(dt)
            assert_equal(res, expected)

    def test_days_property(self):
        self._test_date_properties('days', DAILY)

    def test_months_property(self):
        preprocess_start = lambda d: datetime(d.year, d.month, 1)
        self._test_date_properties('months', MONTHLY, preprocess_start=preprocess_start)

    def test_years(self):
        preprocess_start = lambda d: datetime(d.year, 1, 1)
        self._test_date_properties('years', YEARLY, preprocess_start=preprocess_start)

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

class TestDateAwarePropreties(TestCase):
    def test_day_names_property(self):
        for obj in [DateTimeProxy, Calendar]:
            assert_equal(obj.day_names, WEEKDAYS.values())
            assert_equal(obj.day_names[0], 'Monday')
            assert_equal(obj.day_names[6], 'Sunday')

    def test_day_names_abbr_property(self):
        for obj in [DateTimeProxy, Calendar]:
            assert_equal(obj.day_names_abbr, WEEKDAYS_ABBR.values())
            assert_equal(obj.day_names_abbr[0], 'Mon')
            assert_equal(obj.day_names_abbr[6], 'Sun')

    def test_month_names_property(self):
        for obj in [DateTimeProxy, Calendar]:
            assert_equal(obj.month_names, MONTHS.values())
            assert_equal(obj.month_names[0], 'January')
            assert_equal(obj.month_names[11], 'December')

    def test_month_names_abbr_property(self):
        for obj in [DateTimeProxy, Calendar]:
            assert_equal(Calendar.month_names_abbr, MONTHS_3.values())
            assert_equal(Calendar.month_names_abbr[0], 'jan')
            assert_equal(Calendar.month_names_abbr[11], 'dec')

class TestSimpleProxy(TestCase):
    def setUp(self):
        self.datetime = datetime.now()
        self.proxy = SimpleProxy(self.datetime)

    def test_getattr(self):
        for prop in ('day', 'month', 'year'):
            assert_equal(getattr(self.proxy, prop), getattr(self.datetime, prop))
        proxy_strftime = getattr(self.proxy, 'strftime')
        real_strftime  = getattr(self.datetime, 'strftime')
        arg = '%Y/%m/%d'
        assert_equal(proxy_strftime(arg), real_strftime(arg))

        self.proxy.foo = 'foo'
        assert_equal(self.proxy.foo, 'foo')

    def test_comparisons(self):
        other_proxy = SimpleProxy(self.datetime)
        assert_equal(self.proxy, other_proxy)
        assert other_proxy >= self.proxy
        assert self.proxy <= other_proxy
        other_proxy = other_proxy + timedelta(1)
        assert other_proxy > self.proxy
        assert self.proxy < other_proxy
        other_proxy = other_proxy - timedelta(2)
        assert other_proxy < self.proxy
        assert self.proxy > other_proxy

from calendartools.views import Year, Month, Week, Day, Hour, TripleMonth
import calendar
class TestDateTimeProxies(TestCase):
    def setUp(self):
        self.datetime = datetime(1982, 8, 17)
        self.year     = Year(self.datetime)
        self.month    = Month(self.datetime)
        self.week     = Week(self.datetime)
        self.day      = Day(self.datetime)
        self.hour     = Hour(datetime.combine(self.datetime.date(), time(6, 30, 5)))

    def test_default_datetimeproxy_conversion(self):
        mapping = (
            (date(1982, 8, 17), datetime(1982, 8, 17)),
            (datetime(1982, 8, 17, 6), datetime(1982, 8, 17, 6, 0, 0)),
            (datetime(1982, 8, 17, 6, 30), datetime(1982, 8, 17, 6, 30, 0)),
            (datetime(1982, 8, 17, 6, 30, 5), datetime(1982, 8, 17, 6, 30, 5)),
        )
        for inp, expected in mapping:
            assert_equal(DateTimeProxy(inp).start, expected)

    def test_hour_equality(self):
        equal = (
            datetime(1982, 8, 17, 6, 30, 5),
            datetime(1982, 8, 17, 6, 0, 0),
            datetime(1982, 8, 17, 7, 0, 0) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 17),
            datetime(1982, 8, 17, 6, 0, 0) - timedelta.resolution,
            datetime(1982, 8, 17, 7, 0, 0),
        )
        for dt in equal:
            assert_equal(self.hour, dt)
            assert self.hour >= dt
            assert self.hour <= dt
            assert dt in self.hour
        for dt in not_equal:
            assert_not_equal(self.hour, dt)
            assert_false(dt in self.hour)

    def test_day_equality(self):
        equal = (
            date(1982, 8, 17),
            datetime(1982, 8, 17),
            datetime(1982, 8, 17, 0, 0, 1),
            datetime(1982, 8, 17, 12, 30, 33),
            datetime(1982, 8, 18) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 16),
            date(1982, 8, 18),
            datetime(1982, 8, 16),
            datetime(1982, 8, 17) - timedelta.resolution,
            datetime(1982, 8, 18),
        )
        for dt in equal:
            assert_equal(self.day, dt)
            assert self.day >= dt
            assert self.day <= dt
            assert dt in self.day
        for dt in not_equal:
            assert_not_equal(self.day, dt)
            assert_false(dt in self.day)

    def test_week_equality(self):
        equal = (
            date(1982, 8, 16),
            date(1982, 8, 22),
            datetime(1982, 8, 16),
            datetime(1982, 8, 23) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 15),
            date(1982, 8, 23),
            datetime(1982, 8, 16) - timedelta.resolution,
            datetime(1982, 8, 23),
        )
        for dt in equal:
            assert_equal(self.week, dt)
            assert self.week >= dt
            assert self.week <= dt
            assert dt in self.week
        for dt in not_equal:
            assert_not_equal(self.week, dt)
            assert_false(dt in self.week)

    def test_month_equality(self):
        equal = (
            self.datetime.date(),
            date(1982, 8, 1),
            date(1982, 9, 1) - timedelta(1),
            self.datetime,
            datetime(1982, 8, 1),
            datetime(1982, 9, 1) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 8, 1) - timedelta(1),
            date(1982, 9, 1),
            datetime(1982, 8, 1) - timedelta.resolution,
            datetime(1982, 9, 1),
        )
        for dt in equal:
            assert_equal(self.month, dt)
            assert self.month >= dt
            assert self.month <= dt
            assert dt in self.month
        for dt in not_equal:
            assert_not_equal(self.month, dt)
            assert_false(dt in self.month)

    def test_year_equality(self):
        equal = (
            date(1982, 1, 1),
            date(1982, 12, 31),
            datetime(1982, 1, 1),
            datetime(1983, 1, 1) - timedelta.resolution,
        )
        not_equal = (
            date(1982, 1, 1) - timedelta(1),
            date(1982, 12, 31) + timedelta(1),
            datetime(1982, 1, 1) - timedelta.resolution,
            datetime(1983, 1, 1),
        )
        for dt in equal:
            assert_equal(self.year, dt)
            assert self.year >= dt
            assert self.year <= dt
            assert dt in self.year
        for dt in not_equal:
            assert_not_equal(self.year, dt)
            assert_false(dt in self.year)

    def test_membership(self):
        for i in (self.hour, self.day, self.week, self.month, self.year):
            assert i in self.year
        for i in (self.hour, self.day, self.week, self.month):
            assert i in self.month
        for i in (self.hour, self.day, self.week):
            assert i in self.week
        for i in (self.hour, self.day,):
            assert i in self.day
        for i in (self.hour,):
            assert i in self.hour

        class TenMinuteInterval(DateTimeProxy):
            interval = timedelta(minutes=10)
            def convert(self, dt):
                dt = super(TenMinuteInterval, self).convert(dt)
                return dt.replace(second=0)

        ten_min_period = TenMinuteInterval(datetime(1982, 8, 17, 6, 30, 5))
        good_inputs = (
            datetime(1982, 8, 17, 6, 30),
            datetime(1982, 8, 17, 6, 35),
            datetime(1982, 8, 17, 6, 40) - timedelta.resolution,
        )
        bad_inputs = (
            date(1982, 8, 17),
            datetime(1982, 8, 17, 6, 30) - timedelta.resolution,
            datetime(1982, 8, 17, 6, 40),
        )
        for inp in good_inputs:
            assert_in(inp, ten_min_period)
        for inp in bad_inputs:
            assert_not_in(inp, ten_min_period)

    def test_next(self):
        assert_equal(self.hour.next(),  datetime(1982, 8, 17, 7, 30, 5))
        assert_equal(self.day.next(),   datetime(1982, 8, 18))
        assert_equal(self.week.next(),  datetime(1982, 8, 24))
        assert_equal(self.month.next(), datetime(1982, 9, 17))
        assert_equal(self.year.next(),  datetime(1983, 8, 17))
        assert isinstance(self.hour.next(),  Hour)
        assert isinstance(self.day.next(),   Day)
        assert isinstance(self.week.next(),  Week)
        assert isinstance(self.month.next(), Month)
        assert isinstance(self.year.next(),  Year)

    def test_previous(self):
        assert_equal(self.hour.previous(),  datetime(1982, 8, 17, 5, 30, 5))
        assert_equal(self.day.previous(),   datetime(1982, 8, 16))
        assert_equal(self.week.previous(),  datetime(1982, 8, 10))
        assert_equal(self.month.previous(), datetime(1982, 7, 17))
        assert_equal(self.year.previous(),  datetime(1981, 8, 17))
        assert isinstance(self.hour.previous(),  Hour)
        assert isinstance(self.day.previous(),   Day)
        assert isinstance(self.week.previous(),  Week)
        assert isinstance(self.month.previous(), Month)
        assert isinstance(self.year.previous(),  Year)

    def test_day_hours_iteration(self):
        expected = list(rrule(HOURLY,
            dtstart=datetime(1982, 8, 17),
            until=datetime(1982, 8, 17, 23, 59, 59)
        ))
        actual = list(i for i in self.day.hours)
        assert_equal(expected, actual)
        assert all(isinstance(i, Hour) for i in actual)

    def test_week_days_iterator(self):
        start = datetime(1982, 8, 16) # monday
        expected = list(rrule(DAILY,
            dtstart=start,
            until=(start + timedelta(7)) - timedelta.resolution
        ))
        actual = list(i for i in self.week.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_month_weeks_iterator(self):
        expected = list(rrule(WEEKLY,
            dtstart=datetime(1982, 8, 1),
            until=datetime(1982, 8, 31)
        ))
        actual = list(i for i in self.month.weeks)
        assert_equal(expected, actual)
        assert all(isinstance(i, Week) for i in actual)

    def test_month_days_iterator(self):
        expected = list(rrule(DAILY,
            dtstart=datetime(1982, 8, 1),
            until=datetime(1982, 8, 31)
        ))
        actual = list(i for i in self.month.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_year_months_iterator(self):
        expected = list(rrule(MONTHLY,
            dtstart=datetime(1982, 1, 1),
            until=datetime(1982, 12, 31)
        ))
        actual = list(self.year.months)
        assert_equal(expected, actual)
        assert all(isinstance(i, Month) for i in actual)

    def test_year_days_iterator(self):
        expected = list(rrule(DAILY,
            dtstart=datetime(1982, 1, 1),
            until=datetime(1982, 12, 31)
        ))
        actual = list(self.year.days)
        assert_equal(expected, actual)
        assert all(isinstance(i, Day) for i in actual)

    def test_day_iteration_returns_hours(self):
        assert_equal(list(self.day), list(self.day.hours))

    def test_week_iteration_returns_days(self):
        assert_equal(list(self.week), list(self.week.days))

    def test_month_iteration_returns_weeks(self):
        assert_equal(list(self.month), list(self.month.weeks))

    def test_year_iteration_returns_months(self):
        assert_equal(list(self.year), list(self.year.months))

    def test_names_property(self):
        dayname = calendar.day_name[self.datetime.weekday()]
        assert_equal(dayname, self.day.name)
        assert_equal('August', self.month.name)

    def test_abbr_property(self):
        abbr = calendar.day_abbr[self.datetime.weekday()]
        assert_equal(abbr, self.day.abbr)
        assert_equal('aug', self.month.abbr)

    def test_start_property(self):
        assert_equal(self.hour.start,  datetime(1982, 8, 17, 6))
        assert_equal(self.day.start,   datetime(1982, 8, 17))
        assert_equal(self.week.start,  datetime(1982, 8, 16))
        assert_equal(self.month.start, datetime(1982, 8, 1))
        assert_equal(self.year.start,  datetime(1982, 1, 1))

    def test_finish_property(self):
        smidge = timedelta.resolution
        assert_equal(self.hour.finish,  datetime(1982, 8, 17, 7) - smidge)
        assert_equal(self.day.finish,   datetime(1982, 8, 18) - smidge)
        assert_equal(self.week.finish,  datetime(1982, 8, 23) - smidge)
        assert_equal(self.month.finish, datetime(1982, 9, 1) - smidge)
        assert_equal(self.year.finish,  datetime(1983, 1, 1) - smidge)

    def test_number_property(self):
        assert_equal(self.hour.number,  6)
        assert_equal(self.day.number,   17)
        assert_equal(self.week.number,  self.datetime.isocalendar()[1])
        assert_equal(self.month.number, 8)
        assert_equal(self.year.number,  1982)

    def test_get_methods_for_more_general_periods(self):
        assert not hasattr(self.hour, 'get_hour')
        assert_equal(self.hour.get_day(), self.day)
        assert_equal(self.hour.get_week(), self.week)
        assert_equal(self.hour.get_month(), self.month)
        assert_equal(self.hour.get_year(), self.year)

        assert not hasattr(self.day, 'get_hour')
        assert not hasattr(self.day, 'get_day')
        assert_equal(self.day.get_week(), self.week)
        assert_equal(self.day.get_month(), self.month)
        assert_equal(self.day.get_year(), self.year)

        assert not hasattr(self.week, 'get_hour')
        assert not hasattr(self.week, 'get_day')
        assert not hasattr(self.week, 'get_week')
        assert_equal(self.week.get_month(), self.month)
        assert_equal(self.week.get_year(), self.year)

        assert not hasattr(self.month, 'get_hour')
        assert not hasattr(self.month, 'get_day')
        assert not hasattr(self.month, 'get_week')
        assert not hasattr(self.month, 'get_month')
        assert_equal(self.month.get_year(), self.year)

        assert not hasattr(self.year, 'get_hour')
        assert not hasattr(self.year, 'get_day')
        assert not hasattr(self.year, 'get_week')
        assert not hasattr(self.year, 'get_month')
        assert not hasattr(self.year, 'get_year')

    def test_month_calendar_display_property(self):
        expected = calendar.monthcalendar(self.datetime.year, self.datetime.month)
        actual = self.month.calendar_display
        actual = [[i.day if i else 0 for i in lst] for lst in actual]
        assert_equal(expected, actual)

    def test_intervals(self):
        intervals = self.day.intervals
        expected_start = datetime.combine(
            self.datetime.date(), defaults.TIMESLOT_START_TIME
        )
        expected_end = expected_start + defaults.TIMESLOT_END_TIME_DURATION
        assert_equal(intervals[0],  expected_start)
        assert_equal(intervals[-1], expected_end)

        expected_interval_count = 0
        while expected_start <= expected_end:
            expected_start += defaults.TIMESLOT_INTERVAL
            expected_interval_count += 1
        assert_equal(len(intervals), expected_interval_count)

class TestTripleMonth(TestCase):
    def setUp(self):
        self.datetime = datetime(1982, 8, 17)
        self.trimonth = TripleMonth(self.datetime)
        self.expected = [
            datetime(1982, 8, 1), datetime(1982, 9, 1), datetime(1982, 10, 1)
        ]

    def test_start_and_finish(self):
        assert_equal(self.trimonth.start, self.expected[0])
        assert_equal(self.trimonth.finish, datetime(1982, 11, 1) - timedelta.resolution)

    def test_iterates_over_months(self):
        actual = [i for i in self.trimonth]
        assert_equal(self.expected, actual)

    def test_first_month_property(self):
        assert_equal(self.trimonth.first_month, self.expected[0])

    def test_second_month_property(self):
        assert_equal(self.trimonth.second_month, self.expected[1])

    def test_third_month_property(self):
        assert_equal(self.trimonth.third_month, self.expected[2])


class TestDateTimeProxiesWithOccurrences(TestCase):
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
        Occurrence.objects.create(
            event=self.event,
            start=self.start,
            finish=self.start + timedelta(hours=2)
        )
        Occurrence.objects.create(
            event=self.event,
            start=self.start,
            status=Occurrence.CANCELLED,
            finish=self.start + timedelta(hours=2)
        )

        self.year = Year(self.start, occurrences=Occurrence.objects.all())

    def test_occurrences_populated(self):
        for month in self.year.months:
            if month != self.start:
                assert not month.occurrences
            else:
                assert_equal(len(month.occurrences), 2)
                for day in month.days:
                    if day != self.start:
                        assert not day.occurrences
                    else:
                        assert_equal(len(day.occurrences), 2)
                        for hour in day.hours:
                            if hour != self.start:
                                assert not hour.occurrences
                            else:
                                assert_equal(len(hour.occurrences), 2)

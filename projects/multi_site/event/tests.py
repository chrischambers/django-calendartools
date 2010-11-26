from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from event.models import Calendar, Event, Occurrence

from django.test import TestCase
from calendartools.forms import MultipleOccurrenceForm
from nose.tools import *


class TestMultipleSitesFunctionality(TestCase):
    def setUp(self):
        self.creator = User.objects.create(username='TestyMcTesterson')
        self.main_site = Site.objects.get(domain='example.com') # default
        self.other_site = Site.objects.create(
            domain='foo.com', name='Foo'
        )
        self.calendar = Calendar.objects.create(name='Basic', slug='basic')
        self.event = Event.objects.create(
            name='Event', slug='event', creator=self.creator
        )
        self.start = datetime.now() + timedelta(minutes=30)
        self.finish = self.start + timedelta(hours=2)
        self.occurrence = self.event.add_occurrences(
            self.calendar, self.start, self.finish)[0]

        now = datetime.now()
        self.base_datetime = datetime(now.year + 1, 1, 7)
        self.urls = [
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

    def tearDown(self):
        if hasattr(self, '_original_site_id'):
            from django.conf import settings
            settings.SITE_ID = self._original_site_id
            del self._original_site_id

    def test_calendars_only_from_current_site(self):
        other_site = Site.objects.create(
            domain='foo.com', name='Foo'
        )
        newcal = Calendar.objects.create(name='Foo', slug='foo')
        newcal.sites.clear()
        newcal.sites.add(other_site)
        form = MultipleOccurrenceForm(event=self.event)
        cal_pks = [t[0] for t in form.fields['calendar'].choices]
        assert self.calendar.pk in cal_pks
        assert newcal.pk not in cal_pks

    def switch_sites(self, site_id):
        from django.conf import settings
        if not hasattr(self, '_original_site_id'):
            self._original_site_id = settings.SITE_ID
        settings.SITE_ID = site_id

    def test_current_site_methods(self):
        assert_equal(Calendar.on_site.count(), 1)
        assert_equal(Calendar.objects.on_site.count(), 1)
        assert_equal(Event.on_site.count(), 1)
        assert_equal(Event.objects.on_site.count(), 1)
        assert_equal(Occurrence.on_site.count(), 1)
        assert_equal(Occurrence.objects.on_site.count(), 1)

        self.switch_sites(self.other_site.id)
        assert_equal(Calendar.on_site.count(), 0)
        assert_equal(Calendar.objects.on_site.count(), 0)
        assert_equal(Event.on_site.count(), 0)
        assert_equal(Event.objects.on_site.count(), 0)
        assert_equal(Occurrence.on_site.count(), 0)
        assert_equal(Occurrence.objects.on_site.count(), 0)

    def test_visibility(self):
        assert_equal(Calendar.objects.visible().count(), 1)
        assert_equal(Event.objects.visible().count(), 1)
        assert_equal(Occurrence.objects.visible().count(), 1)
        self.switch_sites(self.other_site.id)
        assert_equal(Calendar.objects.visible().count(), 0)
        assert_equal(Event.objects.visible().count(), 0)
        assert_equal(Occurrence.objects.visible().count(), 0)

        self.event.sites.add(self.other_site)
        self.calendar.sites.add(self.other_site)
        assert_equal(Calendar.objects.visible().count(), 1)
        assert_equal(Event.objects.visible().count(), 1)
        assert_equal(Occurrence.objects.visible().count(), 1)
        self.switch_sites(self.other_site.id)
        assert_equal(Calendar.objects.visible().count(), 1)
        assert_equal(Event.objects.visible().count(), 1)
        assert_equal(Occurrence.objects.visible().count(), 1)

    def test_other_site_events_not_listed(self):
        self.event.sites.clear()
        self.event.sites.add(self.other_site)
        response = self.client.get(reverse('event-list'), follow=True)
        assert_equal(response.status_code, 200)
        assert not response.context['object_list']

    def test_occurrences_with_other_site_calendar_not_displayed(self):
        self.calendar.sites.clear()
        self.calendar.sites.add(self.other_site)
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_calendar_list_does_not_display_other_site_calendars(self):
        response = self.client.get(reverse('calendar-list'), follow=True)
        assert_equal(len(response.context[-1].get('object_list')), 1)
        self.calendar.sites.clear()
        self.calendar.sites.add(self.other_site)
        response = self.client.get(reverse('calendar-list'), follow=True)
        assert_equal(len(response.context[-1].get('object_list')), 0)

    def test_other_site_calendars_not_listed(self):
        self.calendar.sites.clear()
        self.calendar.sites.add(self.other_site)
        for url in self.urls:
            response = self.client.get(reverse(url[0], kwargs=url[1]), follow=True)
            assert_equal(404, response.status_code)

from datetime import datetime, timedelta
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from calendartools.models import Event, Occurrence
from calendartools.forms import EventForm, MultipleOccurrenceForm
from nose.tools import *


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
        self.assertTrue(self.client.login(
            username=self.user.username, password='password')
        )

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
        self.occurrence.status = self.event.INACTIVE
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_not_displayed(self):
        self.occurrence.status = self.event.HIDDEN
        self.occurrence.save()
        response = self.client.get(
            reverse('occurrence-detail',
                    args=(self.event.slug, self.occurrence.pk)), follow=True
        )
        assert_equal(response.status_code, 404)

    def test_hidden_occurrence_detail_displayed_for_permitted_users(self):
        self.occurrence.status = self.event.HIDDEN
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
        self.occurrence.status = self.event.CANCELLED
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

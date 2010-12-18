from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from calendartools import defaults
from calendartools.modelbase import (
    CalendarBase, EventBase, OccurrenceBase, AttendanceBase, CancellationBase
)
from event.managers import (
    CalendarSiteManager, EventSiteManager, OccurrenceSiteManager,
    CalendarCurrentSiteManager, EventCurrentSiteManager,
    OccurrenceCurrentSiteManager
)
from calendartools.validators.defaults import activate_default_validators


class Calendar(CalendarBase):
    sites = models.ManyToManyField(Site, verbose_name=_('sites'),
        related_name='calendars'
    )
    objects = CalendarSiteManager()
    on_site = CalendarCurrentSiteManager()


    class Meta(CalendarBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL

    def save(self, *args, **kwargs):
        super(Calendar, self).save(*args, **kwargs)
        if not self.sites.all():
            current_site = Site.objects.get_current()
            self.sites.add(current_site)


class Event(EventBase):
    sites = models.ManyToManyField(Site, verbose_name=_('sites'),
        related_name='events'
    )
    objects = EventSiteManager()
    on_site = EventCurrentSiteManager()


    class Meta(EventBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL

    def save(self, *args, **kwargs):
        super(Event, self).save(*args, **kwargs)
        if not self.sites.all():
            current_site = Site.objects.get_current()
            self.sites.add(current_site)


class Occurrence(OccurrenceBase):
    calendar = models.ForeignKey('Calendar', verbose_name=_('calendar'),
        related_name='occurrences'
    )
    event = models.ForeignKey('Event', verbose_name=_('event'),
        related_name='occurrences'
    )
    objects = OccurrenceSiteManager()
    on_site = OccurrenceCurrentSiteManager()


    class Meta(OccurrenceBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Attendance(AttendanceBase):
    user = models.ForeignKey(User, verbose_name=_('user'),
        related_name='attendances'
    )
    occurrence = models.ForeignKey(Occurrence, verbose_name=_('occurrence'),
        related_name='attendances'
    )


    class Meta(AttendanceBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Cancellation(CancellationBase):
    attendance = models.OneToOneField(Attendance, verbose_name=_('attendance'),
        related_name='cancellation'
    )


    class Meta(AttendanceBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL

activate_default_validators()

if defaults.NO_URL_TRANSLATION:
    from django.template import add_to_builtins
    add_to_builtins('calendartools.templatetags.url_override')

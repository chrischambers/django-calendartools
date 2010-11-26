from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from calendartools import defaults
from calendartools.modelbase import (
    CalendarBase, EventBase, OccurrenceBase, AttendanceBase, CancellationBase
)
from calendartools.managers import (
    CalendarManager, EventManager, OccurrenceManager
)
from calendartools.validators.defaults import activate_default_validators


class Calendar(CalendarBase):
    objects = CalendarManager()


    class Meta(CalendarBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Event(EventBase):
    objects = EventManager()


    class Meta(EventBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Occurrence(OccurrenceBase):
    calendar = models.ForeignKey('Calendar', verbose_name=_('calendar'),
        related_name='occurrences'
    )
    event = models.ForeignKey('Event', verbose_name=_('event'),
        related_name='occurrences'
    )
    objects = OccurrenceManager()


    class Meta(OccurrenceBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Attendance(AttendanceBase):
    user = models.ForeignKey(User, verbose_name=_('user'),
        related_name='attendance'
    )
    occurrence = models.ForeignKey(Occurrence, verbose_name=_('occurrence'),
        related_name='attendees' # users_attended? user_attendance(s)?
    )


    class Meta(OccurrenceBase.Meta):
        app_label = defaults.CALENDAR_APP_LABEL


class Cancellation(CancellationBase):
    attendance = models.OneToOneField(Attendance, verbose_name=_('attendance'),
        related_name='cancellation'
    )

activate_default_validators()

if defaults.NO_URL_TRANSLATION:
    from django.template import add_to_builtins
    add_to_builtins('calendartools.templatetags.url_override')

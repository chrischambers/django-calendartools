from dateutil import rrule
from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField
)
from threaded_multihost.fields import CreatorField, EditorField
from calendartools import defaults
from calendartools.exceptions import MaxOccurrenceCreationsExceeded
from calendartools.managers import (
    CalendarManager, EventManager, OccurrenceManager
)
from calendartools.signals import (
    collect_occurrence_validators, collect_attendance_validators
)
from calendartools.validators.defaults import activate_default_validators

try:
    from functools import partial
except ImportError: # Python 2.3, 2.4 fallback.
    from django.utils.functional import curry as partial


class AuditedModel(models.Model):
    datetime_created  = CreationDateTimeField(_('Created'))
    datetime_modified = ModificationDateTimeField(_('Last Modified'))
    creator = CreatorField(related_name='%(class)ss_created')
    editor  = EditorField(related_name='%(class)ss_modified')


    class Meta(object):
        abstract = True


class EventBase(AuditedModel):
    """Encapsulates common elements for Calendar/Occurrence/Event models."""
    INACTIVE, HIDDEN, CANCELLED, PUBLISHED = 1, 2, 3, 4
    STATUS_CHOICES = (
        (INACTIVE,  _('Inactive')),
        (HIDDEN,    _('Hidden')),
        (CANCELLED, _('Cancelled')),
        (PUBLISHED, _('Published')),
    )


    class Meta(object):
        abstract = True

    @property
    def status_slug(self):
        """
        Slugs **almost** have the property of being valid css class names:
        this property allows us to style objects according to their status.
        """
        for number, label in self.STATUS_CHOICES:
            if self.status == number:
                break
        return slugify(label.lstrip('1234567890_-'))


class Calendar(EventBase):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    status = models.SmallIntegerField(_('status'),
        choices=EventBase.STATUS_CHOICES,
        default=EventBase.PUBLISHED,
        help_text=_(
            "Toggle calendars inactive rather than deleting them. "
            "Changing a Calendar from 'published' to "
            "inactive/hidden/cancelled will deactivate/hide/cancel "
            "all its events and their occurrences. "
            "Toggling it back to 'published' will restore all of the "
            "Events/Occurrences to their former states."
        )
    )
    objects = CalendarManager()


    class Meta(object):
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendars')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s" % (self.name,)

    @models.permalink
    def get_absolute_url(self):
        return ('calendar-detail', [], {'slug': self.slug})


class Event(EventBase):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    status = models.SmallIntegerField(_('status'),
        choices=EventBase.STATUS_CHOICES,
        default=EventBase.PUBLISHED,
        help_text=_(
            "Toggle events inactive rather than deleting them. "
            "Changing an Event from 'published' to inactive/hidden/cancelled "
            "will deactivate/hide/cancel all its occurrences. "
            "Toggling it back to 'published' will restore all of them to "
            "their former state."
        )
    )
    objects = EventManager()


    class Meta(object):
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s" % (self.name,)

    @models.permalink
    def get_absolute_url(self):
        return ('event-detail', [], {'slug': self.slug})

    def add_occurrences(self, calendar, start, finish, commit=True,
                        **rrule_params):
        '''
        Add one or more occurrences to the event using a comparable API to
        ``dateutil.rrule``. Returns a list of created ``Occurrence`` objects.

        If ``rrule_params`` does not contain a ``freq``, one will be defaulted
        to ``rrule.DAILY``.

        Because ``rrule.rrule`` returns an iterator that can essentially be
        unbounded, we need to slightly alter the expected behavior here in
        order to enforce a finite number of occurrence creation.

        If both ``count`` and ``until`` entries are missing from
        ``rrule_params``, only a single ``Occurrence`` instance will be created
        using the exact ``start`` and ``finish`` values.

        If ``commit`` is ``False``, the ``Occurrence`` objects are not saved to
        the database.
        '''
        rrule_params.setdefault('freq', rrule.DAILY)

        if commit:
            make_occurrence = partial(self.occurrences.create, calendar=calendar)
        else:
            make_occurrence = partial(Occurrence, calendar=calendar, event=self)

        if 'count' not in rrule_params and 'until' not in rrule_params:
            return [make_occurrence(start=start, finish=finish)]
        else:
            creation_count = 0
            occurrences = []
            delta = finish - start
            for ev in rrule.rrule(dtstart=start, **rrule_params):
                if (defaults.MAX_OCCURRENCE_CREATION_COUNT and
                    creation_count >= defaults.MAX_OCCURRENCE_CREATION_COUNT):
                    raise MaxOccurrenceCreationsExceeded
                occurrences.append(make_occurrence(start=ev, finish=ev + delta))
                creation_count += 1
            return occurrences

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED


class PluggableValidationMixin(object):
    """
    Must define ``validation_signal``.
    """
    def collect_and_run_validators(self):
        """Collects all pluggable validation checks and runs them, in order of
        priority."""
        validators = self.validation_signal.send(sender=self)
        validators = [v[1] for v in validators] # instances only
        validators.sort(key=lambda v: v.priority, reverse=True)
        for validator in validators:
            validator.validate()

    def clean(self):
        self.collect_and_run_validators()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(PluggableValidationMixin, self).save(*args, **kwargs)


class Occurrence(PluggableValidationMixin, EventBase):
    calendar = models.ForeignKey(Calendar, verbose_name=_('calendar'),
        related_name='occurrences'
    )
    event = models.ForeignKey(Event, verbose_name=_('event'),
        related_name='occurrences'
    )
    start = models.DateTimeField(_('start'))
    finish = models.DateTimeField(_('finish'))
    status = models.SmallIntegerField(_('status'),
        choices=EventBase.STATUS_CHOICES,
        default=EventBase.PUBLISHED,
        help_text=_('Toggle occurrences inactive rather than deleting them.')
    )
    objects = OccurrenceManager()

    validation_signal = collect_occurrence_validators

    class Meta(object):
        verbose_name = _('Occurrence')
        verbose_name_plural = _('Occurrences')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s @ %s" % (
            self.event.name, self.start.strftime('%Y-%m-%d %H:%M:%S')
        )

    @models.permalink
    def get_absolute_url(self):
        return ('occurrence-detail', [], {
            'slug':   self.event.slug,
            'pk':     self.pk
        })

    def clean(self):
        if not self.start or not self.finish:
            return # to be dealt with by built-in validators
        super(Occurrence, self).clean()

    @property
    def is_cancelled(self):
        return (self.status == self.CANCELLED or
                self.calendar.status == self.calendar.CANCELLED or
                self.event.status == self.event.CANCELLED)

    # Veneers:
    #---------
    @property
    def name(self):
        return self.event.name

    @property
    def description(self):
        return self.event.description


class Attendance(PluggableValidationMixin, AuditedModel):
    INACTIVE, BOOKED, ATTENDED, CANCELLED = 1, 2, 3, 4
    STATUS_CHOICES = (
        (INACTIVE,  _('Inactive')),
        (BOOKED,    _('Booked')),
        (ATTENDED,  _('Attended')),
        (CANCELLED, _('Cancelled')),
    )

    user = models.ForeignKey(User, verbose_name=_('user'),
        related_name='attendance'
    )
    occurrence = models.ForeignKey(Occurrence, verbose_name=_('occurrence'),
        related_name='attendees' # users_attended? user_attendance(s)?
    )
    status = models.SmallIntegerField(_('status'),
        choices=STATUS_CHOICES,
        default=BOOKED,
        help_text=_("Toggle attendance records inactive rather "
                    "than deleting them.")
    )
    validation_signal = collect_attendance_validators


    class Meta(object):
        verbose_name = _('Attendance')
        verbose_name_plural = _('Attendances')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s @ %s" % (self.user.username, self.occurrence.event.name)

    # @models.permalink
    # def get_absolute_url(self):
    #     return ('attendance_record', [], {})

activate_default_validators()

if defaults.NO_URL_TRANSLATION:
    from django.template import add_to_builtins
    add_to_builtins('calendartools.templatetags.url_override')

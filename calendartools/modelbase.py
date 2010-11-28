from dateutil import rrule
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models.loading import get_model
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField
)
from threaded_multihost.fields import CreatorField, EditorField
from calendartools import defaults
from calendartools.exceptions import MaxOccurrenceCreationsExceeded
from calendartools.signals import collect_validators
from calendartools.modelproxy import LocalizedOccurrenceProxy

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
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True


class StatusBase(AuditedModel):
    """Encapsulates common elements for Calendar/Occurrence/Event models."""
    INACTIVE, HIDDEN, CANCELLED, PUBLISHED = 1, 2, 3, 4
    STATUS_CHOICES = (
        (INACTIVE,  _('Inactive')),
        (HIDDEN,    _('Hidden')),
        (CANCELLED, _('Cancelled')),
        (PUBLISHED, _('Published')),
    )


    class Meta(object):
        app_label = defaults.CALENDAR_APP_LABEL
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


class CalendarBase(StatusBase):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    status = models.SmallIntegerField(_('status'),
        choices=StatusBase.STATUS_CHOICES,
        default=StatusBase.PUBLISHED,
        help_text=_(
            "Toggle calendars inactive rather than deleting them. "
            "Changing a Calendar from 'published' to "
            "inactive/hidden/cancelled will deactivate/hide/cancel "
            "all its events and their occurrences. "
            "Toggling it back to 'published' will restore all of the "
            "Events/Occurrences to their former states."
        )
    )


    class Meta(object):
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendars')
        get_latest_by = 'datetime_created'
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True

    def __unicode__(self):
        return u"%s" % (self.name,)

    @models.permalink
    def get_absolute_url(self):
        return ('calendar-detail', [], {'slug': self.slug})


class EventBase(StatusBase):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)
    status = models.SmallIntegerField(_('status'),
        choices=StatusBase.STATUS_CHOICES,
        default=StatusBase.PUBLISHED,
        help_text=_(
            "Toggle events inactive rather than deleting them. "
            "Changing an Event from 'published' to inactive/hidden/cancelled "
            "will deactivate/hide/cancel all its occurrences. "
            "Toggling it back to 'published' will restore all of them to "
            "their former state."
        )
    )


    class Meta(object):
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        get_latest_by = 'datetime_created'
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True

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
            make_occurrence = partial(self.occurrences.model,
                                      calendar=calendar, event=self)

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
    def collect_and_run_validators(self):
        """Collects all pluggable validation checks and runs them, in order of
        priority."""
        validators = collect_validators.send(sender=self.__class__, instance=self)
        validators = [v[1] for v in validators] # instances only
        validators.sort(key=lambda v: v.priority, reverse=True)
        for validator in validators:
            validator.validate()

    def clean(self):
        self.collect_and_run_validators()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(PluggableValidationMixin, self).save(*args, **kwargs)


class OccurrenceBase(PluggableValidationMixin, StatusBase):
    start = models.DateTimeField(_('start'))
    finish = models.DateTimeField(_('finish'), blank=True, help_text=_(
        'if left blank, will default to the start time + %s.' %
        defaults.DEFAULT_OCCURRENCE_DURATION
    ))
    status = models.SmallIntegerField(_('status'),
        choices=StatusBase.STATUS_CHOICES,
        default=StatusBase.PUBLISHED,
        help_text=_('Toggle occurrences inactive rather than deleting them.')
    )


    class Meta(object):
        verbose_name = _('Occurrence')
        verbose_name_plural = _('Occurrences')
        get_latest_by = 'datetime_created'
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True

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
        if (self.start and not self.finish):
            self.finish = self.start + defaults.DEFAULT_OCCURRENCE_DURATION
        if not self.start or not self.finish:
            return # to be dealt with by built-in validators
        super(OccurrenceBase, self).clean()

    @property
    def is_cancelled(self):
        return (self.status == self.CANCELLED or
                self.calendar.status == self.calendar.CANCELLED or
                self.event.status == self.event.CANCELLED)

    def localize(self, timezone):
        return LocalizedOccurrenceProxy(self, timezone=timezone)

    # Veneers:
    #---------
    @property
    def name(self):
        return self.event.name

    @property
    def description(self):
        return self.event.description


class AttendanceBase(PluggableValidationMixin, AuditedModel):
    INACTIVE, BOOKED, ATTENDED, CANCELLED = 1, 2, 3, 4
    STATUS_CHOICES = (
        (INACTIVE,  _('Inactive')),
        (BOOKED,    _('Booked')),
        (ATTENDED,  _('Attended')),
        (CANCELLED, _('Cancelled')),
    )

    status = models.SmallIntegerField(_('status'),
        choices=STATUS_CHOICES,
        default=BOOKED,
        help_text=_("Toggle attendance records inactive rather "
                    "than deleting them. Once an Attendance record "
                    "is cancelled, you should create a new one rather "
                    "than modifying it.")
    )


    class Meta(object):
        verbose_name = _('Attendance Record')
        verbose_name_plural = _('Attendance Records')
        get_latest_by = 'datetime_created'
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True

    def __unicode__(self):
        return u"%s @ %s (%s)" % (
            self.user.username, self.occurrence.event.name,
            self.occurrence.start.strftime('%Y/%m/%d - %H:%M:%S')
        )

    def clean(self):
        super(AttendanceBase, self).clean()
        if self.status != self.CANCELLED and self.is_cancelled:
            raise ValidationError(
                'Attendance records cannot be uncancelled - '
                'please create a new attendance record.'
            )

    @property
    def is_cancelled(self):
        try:
            self.cancellation
            return True
        except ObjectDoesNotExist:
            return False

    def save(self, *args, **kwargs):
        value = super(AttendanceBase, self).save(*args, **kwargs)
        if self.status == self.CANCELLED and not self.is_cancelled:
            Cancellation = get_model(defaults.CALENDAR_APP_LABEL, 'Cancellation')
            Cancellation.objects.create(attendance=self)
        return value


class CancellationBase(AuditedModel):
    reason = models.TextField(_('cancellation reason'), blank=True)

    class Meta(object):
        verbose_name = _('Attendance Cancellation')
        verbose_name_plural = _('Attendance Cancellations')
        get_latest_by = 'datetime_created'
        app_label = defaults.CALENDAR_APP_LABEL
        abstract = True

    def __unicode__(self):
        return u"%s" % (self.attendance)

    def save(self, *args, **kwargs):
        value = super(CancellationBase, self).save(*args, **kwargs)
        if self.attendance.status != self.attendance.CANCELLED:
            self.attendance.status = self.attendance.CANCELLED
            self.attendance.save()
        return value

from dateutil import rrule
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField
)
from threaded_multihost.fields import CreatorField, EditorField
from calendartools.managers import EventManager, OccurrenceManager
from calendartools.signals import collect_occurrence_validators
from calendartools.validators import activate_default_validators


class AuditedModel(models.Model):
    datetime_created  = CreationDateTimeField(_('Created'))
    datetime_modified = ModificationDateTimeField(_('Last Modified'))
    creator = CreatorField(related_name='%(class)ss_created')
    editor  = EditorField(related_name='%(class)ss_modified')


    class Meta(object):
        abstract = True


class EventBase(AuditedModel):
    """Encapsulates common elements for Occurrence/Event models."""
    INACTIVE, HIDDEN, CANCELLED, PUBLISHED = 1, 2, 3, 4
    STATUS_CHOICES = (
        (INACTIVE,  _('Inactive')),
        (HIDDEN,    _('Hidden')),
        (CANCELLED, _('Cancelled')),
        (PUBLISHED, _('Published')),
    )


    class Meta(object):
        abstract = True


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

    def add_occurrences(self, start, finish, **rrule_params):
        '''
        Add one or more occurrences to the event using a comparable API to
        ``dateutil.rrule``.

        If ``rrule_params`` does not contain a ``freq``, one will be defaulted
        to ``rrule.DAILY``.

        Because ``rrule.rrule`` returns an iterator that can essentially be
        unbounded, we need to slightly alter the expected behavior here in
        order to enforce a finite number of occurrence creation.

        If both ``count`` and ``until`` entries are missing from
        ``rrule_params``, only a single ``Occurrence`` instance will be created
        using the exact ``start`` and ``finish`` values.
        '''
        rrule_params.setdefault('freq', rrule.DAILY)

        if 'count' not in rrule_params and 'until' not in rrule_params:
            self.occurrences.create(start=start, finish=finish)
        else:
            delta = finish - start
            for ev in rrule.rrule(dtstart=start, **rrule_params):
                self.occurrences.create(start=ev, finish=ev + delta)

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED


class Occurrence(EventBase):
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
        validators = collect_occurrence_validators.send(sender=self)
        validators = [v[1] for v in validators] # instances only
        validators.sort(key=lambda v: v.priority, reverse=True)
        for validator in validators:
            validator.validate()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Occurrence, self).save(*args, **kwargs)

    @property
    def is_cancelled(self):
        return (self.status == self.CANCELLED or
                self.event.status == self.event.CANCELLED)

activate_default_validators()

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import (
    CreationDateTimeField, ModificationDateTimeField
)
from threaded_multihost.fields import CreatorField, EditorField


class AuditedModel(models.Model):
    datetime_created  = CreationDateTimeField(_('Created'))
    datetime_modified = ModificationDateTimeField(_('Last Modified'))
    creator = CreatorField(related_name='%(class)ss_created')
    editor  = EditorField(related_name='%(class)ss_modified')


    class Meta(object):
        abstract = True


class Event(AuditedModel):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(_('description'), blank=True)


    class Meta(object):
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s" % (self.name,)

    @models.permalink
    def get_absolute_url(self):
        return ('event_detail', [], {'slug': self.slug})


class Occurrence(AuditedModel):
    event = models.ForeignKey(Event, verbose_name=_('event'),
        related_name='occurrences'
    )
    start = models.DateTimeField(_('start'))
    finish = models.DateTimeField(_('finish'))


    class Meta(object):
        verbose_name = _('Occurrence')
        verbose_name_plural = _('Occurrences')
        get_latest_by = 'datetime_created'

    def __unicode__(self):
        return u"%s @ %s" % (self.event.name, self.start.isoformat())

    @models.permalink
    def get_absolute_url(self):
        return ('occurrence_detail', [], {
            'slug':   self.event.slug,
            'pk':     self.pk
        })

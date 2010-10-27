from django.db import models
from django.db.models.query import QuerySet
from calendartools import defaults


class DRYManager(models.Manager):
    """Will try and use the queryset's methods if it cannot find
    its own. This allows you to define your custom filtering/exclusion
    methods in one place only (i.e., a custom QuerySet).

    Excerpted from:
    http://stackoverflow.com/questions/2163151/custom-queryset-and-manager-without-breaking-dry
    """
    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)


class EventQuerySet(QuerySet):
    def visible(self, user=None):
        from calendartools.models import Event
        if user and defaults.view_hidden_events_check(user=user):
            return self.filter(status__gte=Event.HIDDEN)
        else:
            return self.filter(status__gte=Event.CANCELLED)


class OccurrenceQuerySet(QuerySet):
    def visible(self, user=None):
        from calendartools.models import Occurrence
        if user and defaults.view_hidden_occurrences_check(user=user):
            return self.filter(status__gte=Occurrence.HIDDEN)
        else:
            return self.filter(status__gte=Occurrence.CANCELLED)


class EventManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return EventQuerySet(self.model)


class OccurrenceManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return OccurrenceQuerySet(self.model)

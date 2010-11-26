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


class CommonQuerySet(QuerySet):
    @property
    def inactive(self):
        return self.filter(status=self.model.INACTIVE)

    @property
    def hidden(self):
        return self.filter(status=self.model.HIDDEN)

    @property
    def cancelled(self):
        return self.filter(status=self.model.CANCELLED)

    @property
    def published(self):
        return self.filter(status=self.model.PUBLISHED)


class CalendarQuerySet(CommonQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        if user and defaults.view_hidden_calendars_check(user=user):
            return self.filter(status__gte=StatusBase.HIDDEN)
        else:
            return self.filter(status__gte=StatusBase.CANCELLED)


class EventQuerySet(CommonQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        if user and defaults.view_hidden_events_check(user=user):
            return self.filter(status__gte=StatusBase.HIDDEN)
        else:
            return self.filter(status__gte=StatusBase.CANCELLED)


class OccurrenceQuerySet(CommonQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        qset = self.select_related('event', 'calendar')
        if user and defaults.view_hidden_occurrences_check(user=user):
            return (qset.filter(status__gte=StatusBase.HIDDEN) &
                    qset.filter(event__status__gte=StatusBase.HIDDEN) &
                    qset.filter(calendar__status__gte=StatusBase.HIDDEN))
        else:
            return (qset.filter(status__gte=StatusBase.CANCELLED) &
                    qset.filter(event__status__gte=StatusBase.CANCELLED) &
                    qset.filter(calendar__status__gte=StatusBase.CANCELLED))


class CalendarManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return CalendarQuerySet(self.model)


class EventManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return EventQuerySet(self.model)


class OccurrenceManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return OccurrenceQuerySet(self.model)

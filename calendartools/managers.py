from django.db import models
from django.db.models.query import QuerySet, Q
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
            # See http://code.djangoproject.com/ticket/15062
            if attr.startswith('_'):
                raise AttributeError
            return getattr(self.get_query_set(), attr, *args)


class CommonQuerySet(QuerySet):
    @property
    def hidden_statuses(self):
        return [self.model.STATUS.inactive, self.model.STATUS.hidden]

    @property
    def hidden_statuses_for_admins(self):
        return [self.model.STATUS.inactive]

    @property
    def inactive(self):
        return self.filter(status=self.model.STATUS.inactive)

    @property
    def hidden(self):
        return self.filter(status=self.model.STATUS.hidden)

    @property
    def cancelled(self):
        return self.filter(status=self.model.STATUS.cancelled)

    @property
    def published(self):
        return self.filter(status=self.model.STATUS.published)

    def visible(self, user=None):
        if user and defaults.view_hidden_calendars_check(user=user):
            return self.exclude(status__in=self.hidden_statuses_for_admins)
        else:
            return self.exclude(status__in=self.hidden_statuses)


class CalendarQuerySet(CommonQuerySet):
    pass


class EventQuerySet(CommonQuerySet):
    pass


class OccurrenceQuerySet(CommonQuerySet):
    def visible(self, user=None):
        qset = self.select_related('event', 'calendar')
        if user and defaults.view_hidden_occurrences_check(user=user):
            return qset.exclude(
                Q(status__in=self.hidden_statuses_for_admins) |
                Q(event__status__in=self.hidden_statuses_for_admins) |
                Q(calendar__status__in=self.hidden_statuses_for_admins)
            )
        else:
            return qset.exclude(
                Q(status__in=self.hidden_statuses) |
                Q(event__status__in=self.hidden_statuses) |
                Q(calendar__status__in=self.hidden_statuses)
            )


class AttendanceQuerySet(CommonQuerySet):
    @property
    def inactive_statuses(self):
        return [self.model.STATUS.inactive, self.model.STATUS.cancelled]

    @property
    def active(self):
        return self.exclude(status__in=self.inactive_statuses)


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


class AttendanceManager(DRYManager):
    use_for_related_fields = True

    def get_query_set(self):
        return AttendanceQuerySet(self.model)

from calendartools.managers import (
    CommonQuerySet, CalendarQuerySet, EventQuerySet, OccurrenceQuerySet,
    CalendarManager, EventManager, OccurrenceManager
)
from calendartools import defaults
from django.conf import settings


class CommonSiteQuerySet(CommonQuerySet):
    @property
    def on_site(self):
        return super(CommonQuerySet, self).filter(
            sites__id__exact=settings.SITE_ID
        )


class CalendarSiteQuerySet(CommonSiteQuerySet, CalendarQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        if user and defaults.view_hidden_calendars_check(user=user):
            return self.on_site.filter(status__gte=StatusBase.HIDDEN)
        else:
            return self.on_site.filter(status__gte=StatusBase.CANCELLED)


class EventSiteQuerySet(CommonSiteQuerySet, EventQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        if user and defaults.view_hidden_events_check(user=user):
            return self.on_site.filter(status__gte=StatusBase.HIDDEN)
        else:
            return self.on_site.filter(status__gte=StatusBase.CANCELLED)


class OccurrenceSiteQuerySet(CommonSiteQuerySet, OccurrenceQuerySet):
    def visible(self, user=None):
        from calendartools.modelbase import StatusBase
        qset = self.select_related('event', 'calendar').on_site
        if user and defaults.view_hidden_occurrences_check(user=user):
            return (qset.filter(status__gte=StatusBase.HIDDEN) &
                    qset.filter(event__status__gte=StatusBase.HIDDEN) &
                    qset.filter(calendar__status__gte=StatusBase.HIDDEN))
        else:
            return (qset.filter(status__gte=StatusBase.CANCELLED) &
                    qset.filter(event__status__gte=StatusBase.CANCELLED) &
                    qset.filter(calendar__status__gte=StatusBase.CANCELLED))

    @property
    def on_site(self):
        return super(OccurrenceQuerySet, self).filter(
            calendar__sites__id__exact=settings.SITE_ID
        )


class CalendarSiteManager(CalendarManager):
    use_for_related_fields = True

    def get_query_set(self):
        return CalendarSiteQuerySet(self.model)


class CalendarCurrentSiteManager(CalendarSiteManager):
    def get_query_set(self):
        return CalendarSiteQuerySet(self.model).on_site


class EventSiteManager(EventManager):
    use_for_related_fields = True

    def get_query_set(self):
        return EventSiteQuerySet(self.model)


class EventCurrentSiteManager(EventSiteManager):
    def get_query_set(self):
        return EventSiteQuerySet(self.model).on_site


class OccurrenceSiteManager(OccurrenceManager):
    use_for_related_fields = True

    def get_query_set(self):
        return OccurrenceSiteQuerySet(self.model)


class OccurrenceCurrentSiteManager(OccurrenceSiteManager):
    def get_query_set(self):
        return OccurrenceSiteQuerySet(self.model).on_site

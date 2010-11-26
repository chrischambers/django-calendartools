from django.contrib import admin
from calendartools.admin import CalendarAdmin, EventAdmin
from event import forms
from event.models import Calendar, Event

def site_name_list(obj):
    names = list(obj.sites.values_list('name', flat=True))
    if len(names) == 1:
        return "%s." % names[0]
    return ", ".join([n for n in names[:-1]]) + " and %s." % names[-1]
site_name_list.short_description = "Sites"
site_name_list.admin_order_field = "sites__domain"


class CalendarSiteAdmin(CalendarAdmin):
    form = forms.AdminAddCalendarForm
    list_display = ['name', 'slug', 'description', 'status', site_name_list,
                    'datetime_created']


class EventSiteAdmin(EventAdmin):
    form = forms.AdminAddEventForm

admin.site.unregister(Calendar)
admin.site.unregister(Event)

admin.site.register(Calendar, CalendarSiteAdmin)
admin.site.register(Event, EventSiteAdmin)

from django.conf.urls.defaults import *
from calendartools.views import *

info_dict = {
    'template_object_name':  'event',
}
ical_dict = {
    'queryset':            Event.published.all(),
    'date_field':          'start',
    'ical_filename':       'calendar.ics',
    'last_modified_field': 'mod_date',
    'location_field':      'location',
    'start_time_field':    'start_time',
    'end_time_field':      'end_time',
}

urlpatterns += patterns('calendartools.views.vobject',
    url(r'^calendar.ics$', 'icalendar', name='icalendar'),
)


from calendartools.urls.calendars import urlpatterns as calendarpatterns
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r"event/", include('calendartools.urls.events')),
    (r"agenda/", include('calendartools.urls.agenda')),
)
urlpatterns += calendarpatterns

from calendartools.urls.calendar import urlpatterns
from django.conf.urls.defaults import *

urlpatterns += patterns('',
    (r"event/", include('calendartools.urls.events')),
)

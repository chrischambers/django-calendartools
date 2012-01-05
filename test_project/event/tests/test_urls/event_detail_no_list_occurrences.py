from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/$', views.event_detail,
        {'list_occurrences': False}, name='event-detail'),
)


from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.event_list, name='events-list'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/$', views.event_detail, name='event-detail'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/add/$', views.event_create, name='event-create'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/(\d+)/$', views.occurrence_detail,
        name='occurrence-detail'),
)

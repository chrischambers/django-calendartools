from django.conf.urls.defaults import *
from calendartools import views

urlpatterns = patterns('',
    url(r'^$', views.event_list, name='event-list'),
    url(r'^confirm/$', views.confirm_occurrences, name='confirm-occurrences'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/$', views.event_detail, name='event-detail'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/add/$', views.event_create, name='event-create'),
    url(r'^(?P<slug>[-A-Za-z0-9_]+)/(?P<pk>\d+)/$', views.occurrence_detail,
        name='occurrence-detail'),
)

from django.conf.urls.defaults import *
from calendartools import views
from calendartools.urls import urlpatterns

urlpatterns += patterns('',
    url(r'^event/(?P<slug>[-A-Za-z0-9_]+)/(?P<pk>\d+)/show_attending/$',
        views.events.occurrence_detail, name='show-attending'),
)

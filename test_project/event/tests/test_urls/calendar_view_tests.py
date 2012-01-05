from django.conf.urls.defaults import *
from calendartools import views
from calendartools.urls import urlpatterns

urlpatterns += patterns('',
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/no-future/$',
        views.YearView.as_view(allow_future=False),
        name='year-calendar-no-future'),
    url(r'^(?P<slug>[-A-Za-z0-9_]*)/(?P<year>\d{4})/no-empty/$',
        views.YearView.as_view(allow_empty=False),
        name='year-calendar-no-empty'),
)
